# Integração SSO (Keycloak) — Guia Completo

Documentação de referência de como o login via Keycloak (SSO) foi implementado no
backoffice da PaperMoon: arquitetura, ferramentas, bibliotecas, passo a passo de
configuração e troubleshooting. Serve como fonte única de verdade para manutenção
futura — as ADRs (`docs/adrs/0002-*`, `docs/adrs/0003-*`) registram *por que* cada
decisão foi tomada; este documento registra *como* funciona hoje e *como operar*.

---

## 1. Visão geral

- **Escopo:** login de **staff** (`is_staff=True`) no backoffice. Não afeta login de
  clientes/tenants.
- **Modo:** opcional e reversível. Login por e-mail/senha continua funcionando sempre —
  SSO é um método adicional, ativável/desativável em runtime sem deploy.
- **Onde configurar:** Backoffice → **Configurações** (`/backoffice/settings`).
- **Padrão:** OIDC Authorization Code + PKCE, com o Keycloak como Identity Provider e a
  PaperMoon continuando como emissora da sessão (JWT RS256 de sempre, via Simple JWT).

```
┌──────────┐        ┌────────────┐        ┌──────────┐        ┌───────────┐
│ Browser  │───1───▶│  Next.js   │───2───▶│  Django  │───3───▶│ Keycloak  │
│          │        │  (BFF)     │        │  (API)   │        │           │
└──────────┘        └────────────┘        └──────────┘        └───────────┘
     │                                                              │
     │◀─────────────────── 4. redirect com code+state ──────────────
     │
     ▼
┌──────────┐        ┌────────────┐        ┌──────────┐        ┌───────────┐
│ Browser  │───5───▶│  Next.js   │───6───▶│  Django  │───7───▶│ Keycloak  │
│          │        │  (BFF)     │        │  (API)   │        │  (token)  │
└──────────┘        └────────────┘        └──────────┘        └───────────┘
                            │◀──────── 8. {access, refresh} ────────┘
                            ▼
                     9. seta cookies httpOnly, redireciona /backoffice
```

---

## 2. Ferramentas e bibliotecas usadas

| Camada | Ferramenta/lib | Por quê |
|---|---|---|
| Backend — validação de JWT/JWKS | [`PyJWT`](https://pyjwt.readthedocs.io/) 2.9 | Já é dependência transitiva do `djangorestframework-simplejwt`; deixamos explícita no `requirements.txt`. `PyJWKClient` cuida do fetch + cache das chaves públicas do Keycloak (`/protocol/openid-connect/certs`), sem precisar de lib própria de JWKS. |
| Backend — chamadas HTTP ao Keycloak | [`requests`](https://requests.readthedocs.io/) | Já era dependência do projeto (usada por todos os `apps/provisioning/*`). Sem cliente OIDC dedicado (`mozilla-django-oidc` etc.) — ver ADR 0002, seção "Por que não usar uma lib OIDC pronta". |
| Backend — criptografia do `client_secret` em repouso | [`cryptography`](https://cryptography.io/) (`Fernet`) | Já era dependência (usada para gerar as chaves RS256 do JWT). `Fernet` é simétrico, autenticado (AEAD) e simples — suficiente para um segredo administrado por poucas pessoas. Ver `shared/crypto.py`. |
| Backend — cache de config/JWKS/state | Redis, via `django.core.cache` (backend nativo `RedisCache` do Django 4+) | Mesmo Redis já usado pelo Celery/rate-limiting — nenhuma peça nova de infra. |
| Backend — auditoria | `apps.audit` (já existente) | Toda mudança na config de SSO grava `AuditLog(sso_config.updated)`, sem o valor do segredo. |
| Frontend — chamadas à API | `axios` + `@tanstack/react-query` (já eram stack padrão do projeto) | Nenhuma lib nova — `adminService`/`authService` seguem exatamente o padrão dos outros recursos administrativos. |
| Frontend — proxy autenticado | Rota genérica `app/api/proxy/[...path]/route.ts` (já existente) | Os endpoints admin de SSO (`/admin/sso-config/*`) passam por ela automaticamente — não foi preciso escrever proxy dedicado. |

**Nenhuma dependência nova foi adicionada ao projeto** além de tornar explícito o
`PyJWT` (já vinha transitivo). Deliberado: um cliente OIDC fino, escrito com as libs
que o projeto já usa, é mais fácil de auditar do que uma lib de terceiros que assume um
modelo de sessão diferente do BFF+JWT da PaperMoon (ver ADR 0002).

---

## 3. Arquivos — o que cada um faz

### Backend

| Arquivo | Papel |
|---|---|
| `apps/accounts/models.py` → `SSOConfiguration` | Linha única (singleton, `pk=1`) com `enabled`, `issuer`, `client_id`, `client_secret_encrypted`, `updated_at`, `updated_by`. |
| `apps/accounts/migrations/0002_ssoconfiguration.py` | Migration da tabela acima. |
| `shared/crypto.py` | `encrypt_secret()`/`decrypt_secret()` — Fernet, chave derivada de `SECRET_KEY` via SHA-256 (sem segredo adicional pra provisionar). Falha de decrypt (ex: `SECRET_KEY` girou) retorna `""`, nunca lança exceção — degrada pra "SSO não configurado", não derruba a aplicação. |
| `apps/accounts/sso_config.py` | Camada de leitura/escrita da config: `get_sso_config()` (lê do banco, cacheia 30s no Redis), `update_sso_config()` (escreve, invalida cache), `invalidate_sso_config_cache()`. |
| `apps/accounts/oidc.py` | Cliente OIDC: `build_authorize_url()` (gera state/nonce/PKCE, monta a URL do Keycloak), `exchange_code()` (troca o `code` pelo `id_token`, valida assinatura/issuer/audience/nonce via `PyJWKClient`), `test_issuer_connectivity()` (discovery document, usado pelo botão "Testar conexão"). |
| `apps/accounts/views.py` | `SSOLoginView`, `SSOCallbackView` (fluxo de login), `SSOStatusView` (público, só `{enabled}`), `SSOConfigAdminView` (GET/PATCH da config), `SSOConfigTestView` (teste de conectividade). |
| `apps/accounts/urls.py` / `urls_admin.py` | Rotas públicas (`/auth/sso/*`) e admin (`/admin/sso-config/*`). |
| `apps/accounts/admin.py` | Registro no Django Admin — `client_secret_encrypted` é `readonly_fields` (só editável via API, que cuida da criptografia). |
| `shared/schemas.py` | Serializers de request/response (`SSOConfigResponseSerializer`, `SSOConfigUpdateRequestSerializer`, etc.) — só para o schema OpenAPI/drf-spectacular, não fazem parsing de verdade. |
| `shared/throttling.py` | `SSORateThrottle` (login/callback, 20/min) e `SSOTestRateThrottle` (teste de conexão, 10/min). |

### Frontend

| Arquivo | Papel |
|---|---|
| `app/api/auth/sso/route.ts` | BFF: busca a `authorize_url` no Django (server-to-server) e redireciona o browser pro Keycloak. |
| `app/api/auth/sso/callback/route.ts` | BFF: recebe `code`/`state` do redirect do Keycloak, troca no Django, aplica os cookies httpOnly (`applyAuthCookies`), redireciona pro `/backoffice`. |
| `app/api/auth/sso/status/route.ts` | BFF público: repassa `GET /auth/sso/status/` do Django — usado pela tela de login. |
| `app/login/page.tsx` | Botão "Entrar com Keycloak", visível quando `authService.getSSOStatus()` retorna `enabled: true` (via React Query, checado no load da página — sem env var). |
| `app/backoffice/settings/page.tsx` | Tela de configuração: toggle ativar/desativar, campos issuer/client_id/client_secret, redirect URI (read-only, com botão copiar), botão "Testar conexão". |
| `lib/services.ts` | `authService.getSSOStatus()`, `adminService.getSSOConfig()/updateSSOConfig()/testSSOConfig()`. |
| `types/index.ts` | `SSOConfig`, `SSOConfigUpdatePayload`, `SSOTestResult`. |
| `components/layout/sidebar.tsx` | Item de nav "Configurações" na seção Sistema do backoffice. |

---

## 4. Segurança — o que foi pensado

- **PKCE obrigatório**, mesmo com confidential client (defesa em profundidade).
- **`state` e `nonce`** gerados server-side, guardados no Redis com TTL de 5 min,
  **uso único** (deletados no primeiro `exchange_code`) — um `state` reaproveitado
  sempre falha.
- **Validação completa do `id_token`**: assinatura (via JWKS), `iss`, `aud`, `exp`,
  `nonce` — qualquer falha é `SSOExchangeFailedError`, nunca um "passa mesmo assim".
- **JIT provisioning condicionado a grupo (opt-in)**: por padrão (`staff_group`
  em branco), login SSO só autentica e-mails que já existem como `CustomUser` com
  `is_staff=True` — um client Keycloak mal configurado (ou comprometido) não cria
  contas novas nem promove ninguém a staff. Se `staff_group` estiver configurado,
  um e-mail novo só vira staff automaticamente quando a claim `groups` do
  id_token contiver esse grupo — nunca por autenticar com sucesso sozinho. Ver
  seção "Atualização — JIT provisioning condicionado a grupo" no ADR 0002.
- **`client_secret` nunca trafega pro frontend em texto puro** — a API só retorna
  `client_secret_set: bool`. No banco, fica criptografado (Fernet). No Django Admin,
  o campo é `readonly`.
- **Audit log** (`AuditLog(sso_config.updated)`) registra `enabled`/`issuer`/`client_id`
  e se o segredo mudou (`client_secret_changed: bool`) — nunca o valor do segredo.
- **Rate limiting** dedicado: `sso` (20/min, login+callback) e `sso_test` (10/min,
  teste de conectividade).
- **Race condition do config mutável**: como a config agora pode mudar em runtime
  (diferente do desenho original com env vars fixas no processo), `build_authorize_url()`
  grava o `issuer` usado no momento do `/login` dentro do próprio `state` armazenado —
  se o admin trocar a config no meio de um login em andamento, o `/callback` termina
  o fluxo com o issuer original, não com um possivelmente trocado.
- **SSRF do "Testar conexão"**: o endpoint é `is_staff`-only e a finalidade dele é
  literalmente alcançar um Keycloak em rede interna — por isso, ao contrário de
  `shared/public_urls.sanitize_public_url` (usado em contextos públicos), ele **não**
  bloqueia IPs privados. Validação aplicada: só aceita `http://`/`https://`, timeout de
  5s, sem seguir para schemes exóticos.

---

## 5. Como configurar (passo a passo)

### 5.1 No Keycloak

1. Crie (ou use) um realm dedicado a staff, ex. `papermoon-staff`.
2. Crie um client:
   - **Client ID:** `papermoon-backoffice` (ou o nome que preferir)
   - **Client authentication:** `On` (confidential client)
   - **Authentication flow:** `Standard flow` (Authorization Code) habilitado
   - **Valid redirect URIs:** o valor exato mostrado no campo "Redirect URI" da tela
     Configurações do backoffice — algo como
     `https://app.papermoon.com.br/api/auth/sso/callback`
3. Salve e copie o **Client Secret** (aba *Credentials*).
4. (Opcional, recomendado) Restrinja quem pode logar nesse client a usuários/grupos que
   correspondem a e-mails de staff cadastrados na PaperMoon — a PaperMoon já rejeita
   quem não é `is_staff=True`, mas ter os dois lados alinhados evita confusão.
5. **Só se for usar JIT provisioning** (realm compartilhado com outras aplicações/AD,
   onde nem toda conta que autentica deve virar staff): crie um grupo dedicado (ex:
   `papermoon-staff`), adicione a ele só quem deve ter acesso, e anexe ao client um
   mapper de grupo — *Client scopes → (dedicated scope do client) → Add mapper → By
   configuration → Group Membership* — com **"Add to ID token"** ligado e **"Full
   group path"** desligado (nome simples, sem `/` na frente). Sem esse mapper, a
   claim `groups` nunca chega no id_token e o JIT nunca dispara, mesmo com
   `staff_group` preenchido no backoffice.

### 5.2 No Backoffice

1. Acesse **Backoffice → Configurações**.
2. Preencha:
   - **Issuer:** `https://<seu-keycloak>/realms/papermoon-staff`
   - **Client ID:** o mesmo do passo 5.1
   - **Client Secret:** cole o segredo copiado
   - **Staff group** (opcional): nome do grupo criado no passo 5.1.5, se for usar JIT.
     Em branco = só quem já existe como `is_staff=True` consegue logar via SSO.
3. Clique em **Testar conexão** — confirma que o issuer é alcançável e expõe um
   discovery document OIDC válido (**não** testa login completo, ver seção 6).
4. Ative o toggle e clique em **Salvar**.
5. Vá para `/login` e confirme que o botão "Entrar com Keycloak" apareceu — clique nele
   para o teste ponta a ponta de verdade.

### 5.3 Rollback rápido

Desativar o toggle em Configurações desliga o botão de SSO imediatamente (o cache do
status tem TTL de 30s) sem precisar de deploy nem mexer em variável de ambiente.

---

## 6. Limitações conhecidas

- **"Testar conexão" não valida `client_id`/`client_secret`**, só confirma que o
  issuer responde com um discovery document OIDC válido. Validar credenciais de fato
  exige percorrer o Authorization Code flow com um browser real — é exatamente o que o
  botão "Entrar com Keycloak" em `/login` faz.
- **SSO é só para staff.** Login de clientes/tenants não é afetado e não tem esse
  fluxo — ver ADR 0002, seção "Não incluído nesta decisão".
- **Girar `SECRET_KEY` em produção invalida o `client_secret` já salvo** (a chave de
  criptografia é derivada dele). Sintoma: SSO volta a aparecer como não configurado
  mesmo com os campos preenchidos. Correção: reabrir Configurações e salvar o
  `client_secret` de novo (o campo sempre aceita reentrada, mesmo que já estivesse
  preenchido antes).

## 7. Troubleshooting

| Sintoma | Causa provável | Onde olhar |
|---|---|---|
| Botão de SSO não aparece em `/login` | Toggle desativado, ou cache do status (30s) ainda não expirou | Backoffice → Configurações → toggle. Aguardar até 30s ou recarregar a página de login de novo. |
| "Testar conexão" falha com timeout/connection refused | Keycloak não alcançável a partir do container Django (rede/firewall) | Testar `curl {issuer}/.well-known/openid-configuration` a partir do host onde o Django roda. |
| Login redireciona pro Keycloak mas volta com `sso_failed` | `redirect_uri` cadastrado no client do Keycloak não bate com o da PaperMoon, ou `client_secret` errado | Conferir o campo "Redirect URI" na tela de Configurações contra o client do Keycloak, caractere por caractere. |
| Login funciona no Keycloak mas volta com "conta não tem acesso de staff" | O e-mail não existe como `CustomUser.is_staff=True`, **e** (`staff_group` está em branco OU o id_token não trouxe a claim `groups` com esse grupo) | Se for pra criar a conta na hora (JIT): confirmar `staff_group` preenchido em Configurações e o mapper de grupo anexado ao client no Keycloak (passo 5.1.5). Se for pra usar uma conta já existente: confirmar o e-mail retornado pelo Keycloak (claim `email`) contra `CustomUser` no Django Admin. |
| JIT configurado (`staff_group` preenchido) mas conta continua não sendo criada | Mapper de grupo não está anexado ao client, ou "Add to ID token" desligado, ou o nome do grupo não bate (path `/nome` vs nome simples) | Decodificar o id_token (jwt.io) de um login de teste e conferir se a claim `groups` aparece e com qual valor exato; `staff_group` é comparado sem diferenciar `/nome` de `nome`, mas precisa bater no nome. |
| `sso_not_configured` mesmo com tudo preenchido | `SECRET_KEY` girou desde o último save (ver seção 6), ou `enabled=false` | Reabrir Configurações, conferir o toggle, resalvar o `client_secret`. |

---

## 8. Referências

- ADR de decisão original: `docs/adrs/0002-sso-keycloak-staff.md`
- ADR do roadmap mais amplo (OTel, feature flags, Terraform, gRPC): `docs/adrs/0003-portfolio-tech-expansion.md`
- Referência de API: `docs/backend/api.md` (seções "Auth" e "Admin — SSO")
- Roadmap: `CLAUDE.md`, Fase 5
