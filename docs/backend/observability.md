# Observabilidade — Tracing distribuído (OpenTelemetry)

Referência de como o tracing distribuído foi implementado: arquitetura, o que é
instrumentado, como o `OutboxEvent` liga o request HTTP original à task assíncrona
que o processa, e como ver os traces localmente. Ver
`docs/adrs/0003-portfolio-tech-expansion.md`, seção 5.1, para o racional da decisão.

---

## O problema que isso resolve

A cadeia `View → OutboxEvent → Celery task (process_outbox_events) → handler →
API externa` era, antes disso, impossível de rastrear ponta a ponta. Quando um
evento como `customer.created` falhava silenciosamente num handler (ex: Chatwoot
fora do ar), a única pista era `OutboxEvent.last_error` — sem contexto de quanto
tempo o processamento levou, quais outros eventos do mesmo request foram afetados,
ou correlação com o request HTTP que originou tudo.

## Arquitetura

```
Browser/n8n → Django (view) → cria OutboxEvent → responde 200
                  │                    │
             (span "django")     trace_id + span_id
                                  capturados no evento
                                        │
                                        ▼
                          Celery (process_outbox_events, a cada 5s)
                                        │
                      novo span "outbox.process.<event_type>"
                      linkado (Link) ao span original via trace_id/span_id
                                        │
                                        ▼
                      handler chama API externa (Chatwoot, GLPI...)
                          (span "requests" — instrumentado automaticamente)
                                        │
                                        ▼
                              tudo exportado via OTLP/gRPC
                                        │
                                        ▼
                                     Jaeger
                          (coletor + UI — http://localhost:16686)
```

## O que é instrumentado

- **Django** (`opentelemetry-instrumentation-django`) — um span por request HTTP.
- **psycopg2** (`opentelemetry-instrumentation-psycopg2`) — queries Postgres como
  spans filhos do request/task que as disparou.
- **Redis** (`opentelemetry-instrumentation-redis`) — cache/rate-limit/locks.
- **requests** (`opentelemetry-instrumentation-requests`) — a instrumentação que
  mais importa na prática: todos os 19 `apps/provisioning/*` chamam APIs externas
  (Chatwoot, GLPI, Zabbix, Keycloak...) via `requests` — antes disso, uma chamada
  lenta ou instável em qualquer um deles era invisível.
- **Celery** (`opentelemetry-instrumentation-celery`) — ciclo de vida de cada task.

Tudo isso é ativado (ou não) por `OTEL_ENABLED` — ver `shared/tracing.py`. Sem
configuração, cada chamada de instrumentação é um no-op da própria API do
OpenTelemetry (não do SDK) — zero custo real, nunca derruba a aplicação. Mesmo
princípio de fallback graceful usado pelos `apps/provisioning/*` quando faltam
credenciais.

## `OutboxEvent.trace_id` / `span_id`

`shared/models.py::OutboxEvent.save()` captura automaticamente o `trace_id` e
`span_id` do span OpenTelemetry ativo no momento da criação — **sem precisar
tocar nenhum dos 30+ call sites** de `OutboxEvent.objects.create(...)` espalhados
pelo código (`apps/customers/services.py`, `apps/billing/commands.py`,
`apps/subscriptions/commands.py` etc.).

`apps/notifications/tasks.py::process_outbox_events()` (o dispatcher único do
outbox) lê esses dois campos e cria um `Link` do OpenTelemetry apontando de volta
pro span original, antes de chamar os handlers registrados — no Jaeger, isso
aparece como uma referência explícita entre o trace do request e o trace do
processamento assíncrono.

Eventos criados com `OTEL_ENABLED=False` (padrão em testes) ficam com
`trace_id`/`span_id` vazios — o link simplesmente não é criado, sem erro.

## Rodando localmente

```bash
docker compose up -d jaeger   # ou docker compose up -d (sobe junto com o resto)
```

- UI do Jaeger: http://localhost:16686
- `django-api`, `celery-worker` e `celery-beat` já sobem com `OTEL_ENABLED=true`
  apontando pro Jaeger local (`docker-compose.yml`) — nenhuma configuração manual
  necessária em dev.
- Cada processo tem um `service.name` próprio (`papermoon-django`,
  `papermoon-celery-worker`, `papermoon-celery-beat`) — filtre por serviço no
  Jaeger pra distinguir de onde veio o span.

Pra gerar tráfego e ver algo aparecer: qualquer request na API (ex: `GET
/health/`) já gera um trace. Pra ver a correlação outbox → Celery, dispare
qualquer ação que grave um `OutboxEvent` (ex: criar um customer) e espere até 5s
pelo próximo ciclo de `process_outbox_events`.

## Produção

Fora do Docker Compose de dev, defina:

```
OTEL_ENABLED=true
OTEL_SERVICE_NAME=papermoon-django   # (ou -celery-worker / -celery-beat)
OTEL_EXPORTER_OTLP_ENDPOINT=http://<host-do-coletor>:4317
```

Este projeto não roda um coletor de produção próprio — `OTEL_EXPORTER_OTLP_ENDPOINT`
aponta pra onde quer que o coletor (Tempo, Jaeger, ou um OTel Collector real)
esteja hospedado. Deixar `OTEL_ENABLED=false` (padrão) desliga tudo sem precisar
remover nenhuma instrumentação do código.

## Referências

- Setup: `backend/shared/tracing.py`
- Modelo: `backend/shared/models.py` (`OutboxEvent`)
- Consumer com linking: `backend/apps/notifications/tasks.py`
- Decisão original: `docs/adrs/0003-portfolio-tech-expansion.md`, seção 5.1
