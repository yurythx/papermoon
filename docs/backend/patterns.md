# PaperMoon Backend — Padrões de Arquitetura

Este documento descreve os padrões arquiteturais adotados no backend da PaperMoon, como eles se relacionam entre si e onde cada um vive no código.

---

## Índice

1. [Visão Geral](#visão-geral)
2. [SOLID](#solid)
3. [CQRS — Command Query Responsibility Segregation](#cqrs)
4. [Transactional Outbox](#transactional-outbox)
5. [Event-Driven com Message Broker](#event-driven)
6. [Multi-Tenant](#multi-tenant)
7. [Unified Response Contract](#unified-response-contract)
8. [State Machine](#state-machine)
9. [Fluxo de Ponta a Ponta](#fluxo-de-ponta-a-ponta)

---

## Visão Geral

```
Request → View → Service/Command → Repository → DB
                      ↓
               OutboxEvent (mesma transaction)
                      ↓ (assíncrono, Celery)
         NotificationsDispatcher → Handlers registrados
                      ↓
           Email / Chatwoot / Licensing
```

Toda escrita passa por uma **transação atômica** que persiste tanto o dado principal quanto um `OutboxEvent`. O Celery consome esses eventos de forma assíncrona e resiliente, sem bloquear a request do usuário.

---

### S — Single Responsibility

Cada camada tem **uma única razão para mudar**:

| Camada | Responsabilidade | Exemplo |
|--------|-----------------|---------|
| `models.py` | Estrutura de dados + constraints de banco | `Customer`, `Invoice` |
| `repositories.py` | Acesso ao banco (ORM) | `DjangoCustomerRepository` |
| `services.py` | Regras de negócio + publicação de eventos | `CustomerService` |
| `commands.py` | Caso de uso write isolado (billing) | `ConfirmPaymentCommand` |
| `queries.py` | Caso de uso read isolado (billing) | `get_financial_metrics()` |
| `views_*.py` | HTTP: valida entrada, delega, formata resposta | `CustomerListCreateView` |
| `handlers.py` | Reação a eventos do Outbox | `create_license_quota()` |
| `tasks.py` | Celery: entrega assíncrona | `process_outbox_events` |

### O — Open/Closed

Novos comportamentos são adicionados **sem modificar código existente**:

- Para suportar um novo canal de notificação (ex: SMS), cria-se `apps/notifications/channels/sms.py` e um novo `@register("payment.failed")`.
- Para suportar um novo gateway de pagamento, cria-se `apps/billing/gateway/stripe_adapter.py` implementando `AbstractPaymentGateway`.
- Nenhum código existente precisa ser alterado.

### L — Liskov Substitution

`DjangoCustomerRepository` implementa `AbstractCustomerRepository`. Qualquer código que depende da abstração (`CustomerService`) continua funcionando se a implementação for trocada (ex: por um repositório de testes com `MagicMock`).

```python
# Teste unitário — comportamento idêntico, implementação trocada
service = CustomerService(MagicMock(spec=AbstractCustomerRepository))
```

### I — Interface Segregation

O repositório de Customer é dividido em **duas interfaces mínimas**:

```python
# apps/customers/interfaces.py

class AbstractCustomerReadRepository(ABC):
    def get_by_id(self, customer_id: UUID) -> Customer: ...
    def get_all(self) -> QuerySet: ...

class AbstractCustomerWriteRepository(ABC):
    def create(self, data: dict) -> Customer: ...
    def update(self, customer_id: UUID, data: dict) -> Customer: ...
    def save(self, customer: Customer) -> Customer: ...

class AbstractCustomerRepository(
    AbstractCustomerReadRepository,
    AbstractCustomerWriteRepository
): ...
```

Código que só precisa de leitura recebe `AbstractCustomerReadRepository`. Código que precisa de escrita recebe `AbstractCustomerWriteRepository`. Nenhum módulo é forçado a depender de métodos que não usa.

### D — Dependency Inversion

Views e services **nunca** instanciam repositórios diretamente no meio da lógica. As dependências entram pelo construtor:

```python
# CORRETO — injeção pelo construtor
class CustomerService:
    def __init__(self, repository: AbstractCustomerRepository) -> None:
        self._repo = repository

# CORRETO — view usa factory local (ponto único de wiring)
def _service() -> CustomerService:
    return CustomerService(DjangoCustomerRepository())
```

O ponto de composição (`DjangoCustomerRepository()`) existe apenas nas views e nos testes — nunca espalhado pela lógica de negócio.

---

## CQRS

**Command Query Responsibility Segregation** — leituras e escritas usam caminhos separados.

### Queries (leitura pura)

- Arquivo: `apps/billing/queries.py`
- Funções puras, sem efeitos colaterais, sem OutboxEvent
- Retornam dados, nunca alteram estado

```python
# apps/billing/queries.py
def get_financial_metrics(customer_id: UUID) -> dict:
    qs = Invoice.objects.filter(customer_id=customer_id)
    return {
        "total_paid": qs.filter(status="paid").aggregate(...)["total"] or 0,
        ...
    }
```

- Métodos de leitura no service também são queries: `list_customers()`, `get_customer()`

### Commands (escrita + evento)

- Arquivo: `apps/billing/commands.py`, métodos no `CustomerService`
- **Sempre** dentro de `@transaction.atomic`
- **Sempre** criam um `OutboxEvent` na mesma transação
- **Nunca** fazem chamadas HTTP dentro da transação

```python
# apps/billing/commands.py
class ConfirmPaymentCommand:
    @transaction.atomic
    def execute(self) -> Invoice:
        invoice = Invoice.objects.select_for_update(skip_locked=True).get(...)
        if invoice.status == Invoice.Status.PAID:
            return invoice          # Idempotente
        invoice.status = Invoice.Status.PAID
        invoice.save()
        OutboxEvent.objects.create(  # Mesmo bloco atômico
            event_type="payment.processed",
            payload={"invoice_id": str(invoice.id), "customer_id": str(invoice.customer_id)},
        )
        return invoice
```

### Regra de ouro

> Um método que retorna dados **não deve** alterar estado.  
> Um método que altera estado **não precisa** retornar dados de negócio (pode retornar a entidade para conveniência, mas não para fluxo de controle).

### HTTP fora de transação

Chamadas HTTP (ex: Asaas) **nunca** ocorrem dentro de `@transaction.atomic`:

```python
class RegisterChargeCommand:
    def execute(self) -> Invoice:
        invoice = Invoice.objects.get(pk=self._invoice_id)
        if invoice.asaas_id:
            return invoice                    # Idempotente

        result = self._gateway.create_charge(...)  # HTTP FORA da transação

        with transaction.atomic():            # Transação CURTA — só escrita
            invoice = Invoice.objects.select_for_update(skip_locked=True).get(...)
            invoice.asaas_id = result["id"]
            invoice.save()
            OutboxEvent.objects.create(...)
        return invoice
```

**Por quê?** Se o HTTP succeeder mas o commit falhar, o Asaas tem a cobrança mas o banco não. Com o HTTP fora, o pior cenário é: HTTP falhou → transação nem começou → retry seguro.

---

## Transactional Outbox

O padrão **Outbox** garante que eventos de domínio **nunca se percam**, mesmo que o broker Celery esteja temporariamente indisponível.

### Modelo

```python
# shared/models.py
class OutboxEvent(models.Model):
    id           = UUIDField(primary_key=True)
    event_type   = CharField(max_length=255)   # ex: "customer.created"
    payload      = JSONField                   # dados do evento
    processed    = BooleanField(default=False, db_index=True)
    processed_at = DateTimeField(null=True)
    retry_count  = IntegerField(default=0)
    last_error   = TextField(null=True)
    failed_at    = DateTimeField(null=True)
```

### Contrato de criação

O `OutboxEvent` **sempre** é criado na mesma `transaction.atomic()` da operação principal:

```python
# CORRETO
@transaction.atomic
def suspend_customer(self, customer_id):
    customer.status = "suspended"
    self._repo.save(customer)          # Escrita principal
    OutboxEvent.objects.create(        # Mesmo bloco — commit ou rollback juntos
        event_type="customer.suspended",
        payload={"customer_id": str(customer.id)},
    )
```

```python
# ERRADO — evento pode ser criado sem a operação principal ter persistido
customer.status = "suspended"
customer.save()
OutboxEvent.objects.create(...)  # Fora de transação — pode falhar independentemente
```

### Consumer

```python
# apps/notifications/tasks.py
@shared_task
def process_outbox_events() -> None:
    with transaction.atomic():
        events = (
            OutboxEvent.objects
            .select_for_update(skip_locked=True)   # Evita processamento duplo
            .filter(processed=False, retry_count__lt=5)
            .order_by("created_at")[:50]
        )
        for event in events:
            for handler in get_handlers(event.event_type):
                handler(event.payload, str(event.id))  # event_id para idempotência
            event.processed = True
            event.processed_at = now()
            event.save()
```

- `select_for_update(skip_locked=True)` — múltiplos workers Celery nunca processam o mesmo evento
- Retry com backoff: `retry_count` incrementado a cada falha, máximo 5
- Limpeza: `cleanup_old_outbox_events` remove eventos processados com mais de 30 dias

---

## Event-Driven

### Registry de Handlers

O núcleo do sistema de eventos é o registry em `apps/notifications/registry.py`:

```python
# apps/notifications/registry.py
_REGISTRY: dict[str, list[HandlerFn]] = {}

def register(event_type: str) -> Callable:
    """Decorator que registra um handler para um event_type."""
    def decorator(fn):
        _REGISTRY.setdefault(event_type, []).append(fn)
        return fn
    return decorator
```

### Registro de handlers

Cada app registra seus handlers no arquivo `handlers.py`:

```python
# apps/licensing/handlers.py
@register("customer.created")
def create_license_quota(payload: dict, event_id: str) -> None:
    LicenseQuota.objects.get_or_create(customer_id=payload["customer_id"], ...)

# apps/support/handlers.py
@register("customer.created")
def provision_chatwoot(payload: dict, event_id: str) -> None:
    ProvisionCustomerCommand(payload["customer_id"]).execute()

# apps/notifications/handlers.py
@register("payment.processed")
def email_payment_confirmed(payload: dict, event_id: str) -> None:
    send_payment_confirmed_email.delay(payload["invoice_id"], event_id)
```

### Auto-discovery

Os handlers são importados automaticamente no `AppConfig.ready()`:

```python
# apps/notifications/apps.py
class NotificationsConfig(AppConfig):
    def ready(self) -> None:
        import apps.licensing.handlers
        import apps.notifications.handlers  # também importa apps.provisioning.handlers
        import apps.support.handlers
```

> `apps/notifications/handlers.py` importa `apps.provisioning.handlers` no topo do módulo, então o
> `ready()` acima registra na prática 4 módulos de handlers (licensing, notifications, support,
> provisioning), não só os 3 que aparecem no import direto.

### Mapa de eventos atual

Mais de 20 event_types ativos, com até 4 handlers cada (e-mail, in-app, licensing, provisioning).
Tabela completa e atualizada em [`docs/backend/architecture.md`](architecture.md) — não duplicada
aqui para evitar desatualização.

### Idempotência nos handlers

Todo handler deve ser **seguro para re-execução**:

```python
# get_or_create previne duplicata mesmo em retry
LicenseQuota.objects.get_or_create(customer_id=..., defaults={...})

# bulk update é idempotente por natureza
ApiKey.objects.filter(customer_id=...).update(is_active=False)

# Email task usa get_or_create com outbox_event_id como chave
notification, created = Notification.objects.get_or_create(
    outbox_event_id=event_id,
    channel="email",
    defaults={...},
)
if not created and notification.status == "sent":
    return  # Já entregue
```

---

## Multi-Tenant

Toda entidade de negócio tem FK para `Customer`. A segregação é enforced nas views:

```python
# apps/customers/views_client.py — tenant vem do usuário logado
def _resolve_customer(user):
    profile = CustomerProfile.objects.filter(user=user).select_related("customer").first()
    if not profile:
        raise NotFound(...)
    return profile.customer

class ClientInvoiceListView(APIView):
    def get(self, request):
        customer = _resolve_customer(request.user)  # Tenant sempre do JWT
        return Response(list_invoices(customer.id, ...))
```

**Regra:** views em `views_client.py` filtram **sempre** pelo customer do usuário logado. Views em `views_admin.py` exigem `IsAdminUser` e acessam qualquer tenant.

---

## Unified Response Contract

Toda resposta da API segue o contrato implementado em `shared/renderers.py`:

```json
// Sucesso
{
  "success": true,
  "data": { ... },
  "error": null
}

// Erro
{
  "success": false,
  "data": null,
  "error": {
    "code": "string_snake_case",
    "message": "Mensagem legível.",
    "details": ["lista opcional"]
  }
}
```

O `UnifiedResponseRenderer` encapsula automaticamente qualquer response do DRF. O `custom_exception_handler` em `shared/exceptions.py` mapeia exceções Django/DRF para códigos de erro semânticos.

---

## State Machine

O `CustomerService` enforça transições de estado válidas via `_TRANSITIONS`:

```python
_TRANSITIONS = {
    "active":    ["suspended", "cancelled"],
    "suspended": ["active",    "cancelled"],
    "cancelled": [],                          # Terminal — sem saída
}

def _assert_transition(self, customer, target):
    if target not in _TRANSITIONS[customer.status]:
        raise ValueError(f"Transição inválida: {customer.status} → {target}.")
```

Qualquer tentativa de transição inválida retorna HTTP 400 com `code: "invalid_transition"`.

---

## Fluxo de Ponta a Ponta

### Exemplo: criação de customer

```
POST /api/v1/admin/customers/
        ↓
CustomerListCreateView.post()
  → serializer.is_valid()
  → CustomerService.create_customer(data)
        ↓ @transaction.atomic
        → DjangoCustomerRepository.create(data)  → INSERT customers
        → OutboxEvent.objects.create(             → INSERT shared_outbox_events
            event_type="customer.created",
            payload={customer_id, plan_id}
          )
        ↓ commit
  → log_action("customer.created", ...)  → INSERT audit_logs
  → Response(CustomerSerializer(customer).data)

        ↓ (5 segundos depois, Celery)
process_outbox_events()
  → select_for_update(skip_locked=True)
  → get_handlers("customer.created") → [create_license_quota, provision_chatwoot]
  → create_license_quota({customer_id})  → INSERT licensing_quotas
  → provision_chatwoot({customer_id})    → HTTP POST chatwoot/api/v1/accounts
  → event.processed = True
```

### Exemplo: pagamento confirmado

```
POST /api/v1/webhooks/asaas/
  Header: asaas-access-token: <token>
        ↓ token validado
  body.event = "PAYMENT_RECEIVED"
        ↓
ConfirmPaymentCommand(invoice.id).execute()
        ↓ @transaction.atomic
        → Invoice.select_for_update(skip_locked=True)
        → if status == PAID: return  ← idempotente
        → invoice.status = "paid" → UPDATE billing_invoices
        → OutboxEvent.create(event_type="payment.processed", ...)
        ↓ commit

        ↓ (5 segundos depois, Celery)
process_outbox_events()
  → email_payment_confirmed(payload, event_id)
        ↓
send_payment_confirmed_email.delay(invoice_id, event_id)
        ↓ (Celery, retry até 3x)
  → Notification.get_or_create(outbox_event_id=event_id, channel="email")
  → if already sent: return  ← idempotente
  → send_mail(...)
  → notification.status = "sent"
```

---

## Adicionando um Novo Evento

1. Crie o evento no service/command:
   ```python
   OutboxEvent.objects.create(
       event_type="meu.evento",
       payload={"id": str(obj.id)},
   )
   ```

2. Crie um handler no app responsável:
   ```python
   # apps/meu_app/handlers.py
   @register("meu.evento")
   def handle_meu_evento(payload: dict, event_id: str) -> None:
       ...
   ```

3. Importe o handler no `NotificationsConfig.ready()`:
   ```python
   import apps.meu_app.handlers
   ```

Nenhum outro arquivo precisa ser modificado. O dispatcher em `process_outbox_events` roteará automaticamente.
