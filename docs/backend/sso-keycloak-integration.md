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
| `apps/accounts/oidc.py` | Cliente OIDC: `build_authorize_url()` (gera state/nonce/PKCE, monta a URL do Keycloak), `exchange_code()` (troca o `code` pelo `id_token`, valida assinatura/issuer/audience/nonce via `PyJWKClient`), `test_issuer_connectivity()` (discovery document, usado pelo botão "Testar conexão"), `group_authorizes_staff()` (compara a claim `groups` do id_token contra `staff_group` — **lista separada por vírgula de nomes de grupo**, `OR` entre eles; ver seção 8). |
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
  id_token contiver **algum** dos grupos configurados — nunca por autenticar com
  sucesso sozinho. `staff_group` é uma **lista separada por vírgula**
  (`"Grupo A,Grupo B,Grupo C"`), não um único nome — necessário em qualquer
  Keycloak que não tenha (e não deva ganhar) um grupo dedicado só pra PaperMoon;
  ver seção 8 pro caso real e a regra de negócio por trás disso. Comparação
  ignora maiúsculas/minúsculas, barra inicial (`/Grupo` vs `Grupo`) e espaços
  internos duplicados. Ver também "Atualização — JIT provisioning condicionado a
  grupo" e "Atualização — staff_group vira lista" no ADR 0002.
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
     `https://papermoon.cloud/api/auth/sso/callback`
3. Salve e copie o **Client Secret** (aba *Credentials*).
4. (Opcional, recomendado) Restrinja quem pode logar nesse client a usuários/grupos que
   correspondem a e-mails de staff cadastrados na PaperMoon — a PaperMoon já rejeita
   quem não é `is_staff=True`, mas ter os dois lados alinhados evita confusão.
5. **Só se for usar JIT provisioning:**
   - **Caso ideal — realm dedicado à PaperMoon:** crie um grupo próprio (ex:
     `papermoon-staff`), adicione só quem deve ter acesso, e anexe ao client um
     mapper de grupo — *Client scopes → (dedicated scope do client) → Add mapper →
     By configuration → Group Membership* — com **"Add to ID token"** ligado e
     **"Full group path"** desligado (nome simples, sem `/` na frente).
   - **Caso realista — realm de terceiro com AD/LDAP já populado (ex: Prefeitura,
     empresa cliente):** você **não** vai poder (nem deve) criar um grupo novo
     chamado "papermoon-*" na árvore organizacional de outra empresa — a regra de
     negócio correta é autorizar por **grupos que já existem e já significam algo**
     pra aquela organização (ex: "time de TI", "administradores de domínio"). Nesse
     caso, `staff_group` no backoffice recebe **vários nomes separados por vírgula**
     em vez de um só — ver seção 8 pro passo a passo completo desse cenário, que é o
     mais comum em produção com clientes reais.
   - **Nos dois casos**, o client precisa do mapper de grupo. Se o Keycloak
     acusar `Invalid parameter value for: scope` / `Invalid scopes: ... groups` ao
     tentar logar, o problema não é o mapper — é que **não existe um *client scope*
     chamado `groups` no realm**, e o backend sempre pede `scope=openid email
     profile groups` na URL de autorização (não é configurável). Crie um client
     scope `groups` (protocolo `openid-connect`) no realm e associe-o ao client
     como scope opcional — ver seção 8, passo 2, pro comando exato via `kcadm.sh`.
     Sem isso, a claim `groups` nunca chega no id_token e o JIT nunca dispara,
     mesmo com `staff_group` preenchido no backoffice.

### 5.2 No Backoffice

1. Acesse **Backoffice → Configurações**.
2. Preencha:
   - **Issuer:** `https://<seu-keycloak>/realms/papermoon-staff`
   - **Client ID:** o mesmo do passo 5.1
   - **Client Secret:** cole o segredo copiado
   - **Staff group** (opcional): nome do grupo criado no passo 5.1.5, se for usar JIT.
     Em branco = só quem já existe como `is_staff=True` consegue logar via SSO.
     Aceita **vários grupos separados por vírgula** (`"Grupo TI,Domain Admins"`) —
     login libera pra quem estiver em **qualquer um** deles.
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
| Clica em "Entrar com Keycloak" e a página do **Keycloak** já dá erro antes de pedir usuário/senha | `redirect_uri` que a PaperMoon envia não está cadastrado no client (**tier 1** — ver seção 8.5); log do Keycloak mostra `type="LOGIN_ERROR" ... error="invalid_redirect_uri"` | Conferir se `FRONTEND_URL`/domínio configurado no `.env` de produção é **exatamente** o domínio público real (`getent hosts`/`curl -I` no domínio — não assumir). Depois comparar com "Valid redirect URIs" do client no Keycloak, caractere por caractere. |
| Clica em "Entrar com Keycloak" e a página do **Keycloak** dá erro tipo "parâmetro scope inválido" | Não existe um *client scope* chamado `groups` associado ao client (**tier 1**); log do Keycloak mostra `KC-SERVICES0093: Invalid parameter value for: scope` + `Invalid scopes: ... groups` | Criar/associar o client scope `groups` — ver seção 8.5, passo 2. |
| Login **funciona** no Keycloak (pede e aceita usuário/senha) mas o PaperMoon volta com "conta não tem acesso de staff" (403) | Chegou no **tier 2** (ver seção 8.5): token exchange OK, mas o e-mail não existe como `CustomUser.is_staff=True` **e** (`staff_group` vazio OU nenhum grupo do id_token bate com os configurados) | Ver linha seguinte + seção 8 pra decidir qual grupo real do IdP deveria autorizar. |
| JIT configurado (`staff_group` preenchido) mas conta continua não sendo criada | Mapper de grupo não anexado ao client (ou client scope `groups` ausente — ver acima), "Add to ID token" desligado, ou nenhum dos grupos em `token_groups` bate com nenhum de `staff_group` | Consultar os grupos reais do usuário via `kcadm.sh get users/{id}/groups` (não confiar de olho — nome pode ter espaço duplicado, ver seção 8.4) e comparar com a lista em `staff_group`. `group_authorizes_staff()` ignora case/barra inicial/espaço duplicado, mas o nome em si precisa bater. |
| `sso_not_configured` mesmo com tudo preenchido | `SECRET_KEY` girou desde o último save (ver seção 6), ou `enabled=false` | Reabrir Configurações, conferir o toggle, resalvar o `client_secret`. |

---

## 8. Caso real: Keycloak de terceiro com AD, sem grupo dedicado à PaperMoon

Runbook completo de uma integração real (cliente com Keycloak próprio, federado com
Active Directory via LDAP, ~680 grupos organizacionais já existentes, nenhum deles
relacionado à PaperMoon). Serve de exemplo pra qualquer integração parecida — a
sequência de sintomas tende a se repetir na mesma ordem porque cada camada só
consegue reportar erro depois que a anterior passa.

### 8.1 Regra de negócio

> Só pode logar no backoffice via SSO quem já é staff cadastrado na PaperMoon, **ou**
> quem pertence a um dos grupos organizacionais do cliente que representam "equipe
> técnica"/"administração" — nunca qualquer conta que simplesmente exista no AD.

Isso descartou de saída a opção mais simples ("criar um grupo `papermoon-staff` no AD
deles") — não é apropriado pedir pra um cliente criar e manter um grupo artificial só
pra uma integração externa, e a resposta certa do ponto de vista de negócio é
reaproveitar a estrutura de acesso que **já** existe e já tem dono (a equipe de TI
deles decide quem entra em "Grupo Nucleo de TI", não a PaperMoon).

### 8.2 Arquitetura do ambiente (generaliza pra qualquer cliente nesse molde)

```
AD/LDAP (fonte da verdade dos grupos)
     │  sync periódico (LDAPStorageProviderFactory, a cada 5 min neste caso)
     ▼
Keycloak (realm do cliente, ex: "Prefeitura")
     │  client "papermoon" (confidential, standard flow)
     │  id_token carrega claim `groups` via protocol mapper
     ▼
PaperMoon (SSOConfiguration.staff_group = allow-list)
```

Ponto-chave: a PaperMoon **nunca** fala com o AD/LDAP diretamente — só enxerga o que
o Keycloak decide colocar na claim `groups` do id_token. Qualquer diagnóstico começa
checando o que essa claim realmente carrega, não supondo.

### 8.3 A ordem em que os bugs aparecem (e por quê é sempre essa ordem)

Um fluxo OIDC malconfigurado falha em camadas — cada camada só é alcançada depois
que a anterior é corrigida, então o mesmo teste ("clica em Entrar com Keycloak")
produz um erro *diferente* a cada rodada de correção. Isso confunde quem tá
debugando pela primeira vez (parece que "trocou de bug" aleatoriamente); na
verdade é sempre esta ordem:

1. **`redirect_uri` errado** → Keycloak rejeita **antes** de mostrar a tela de login.
2. **`scope` com valor não reconhecido** → Keycloak rejeita **antes** de mostrar a
   tela de login (mesmo sintoma visual do #1 pro usuário: nunca chega a digitar
   senha).
3. **Grupo não autoriza** → só aparece **depois** de logar de verdade no Keycloak,
   porque é a PaperMoon (não o Keycloak) quem rejeita, no `POST /callback`.

### 8.4 Bug #1 — domínio errado no `redirect_uri` (`invalid_redirect_uri`)

**Sintoma:** usuário clica em "Entrar com Keycloak", é mandado pro Keycloak, e a
tela trava/erra ali mesmo — nunca chega a pedir usuário/senha.

**Log do Keycloak** (`docker logs <container_keycloak>`):
```
WARN [org.keycloak.events] type="LOGIN_ERROR" ... clientId="papermoon"
     error="invalid_redirect_uri" redirect_uri="http://192.168.1.102:3000/api/auth/sso/callback"
```

**Causa real encontrada:** `FRONTEND_URL` no `.env` de produção apontava pro IP
interno da LAN, não pro domínio público real por trás do proxy/túnel — o
`redirect_uri` que a PaperMoon manda pro Keycloak é sempre
`f"{FRONTEND_URL}/api/auth/sso/callback"` (`apps/accounts/sso_config.py`), então um
`FRONTEND_URL` desatualizado quebra o SSO mesmo com tudo mais certo. Pra piorar,
descobrimos que **o próprio domínio assumido durante a configuração inicial estava
errado** (um subdomínio que nunca existiu no DNS) — a lição: **nunca assumir qual é
o domínio público real; confirmar com `getent hosts <domínio>` + `curl -I
https://<domínio>/` e conferir um header/conteúdo que só a aplicação certa
devolveria** antes de configurar qualquer `redirect_uri`.

**Correção:** alinhar `FRONTEND_URL` (e `NEXT_PUBLIC_SITE_URL`/`CORS_ALLOWED_ORIGINS`
junto, já que sofrem do mesmo tipo de desatualização) ao domínio público real e
confirmado, redeployar, e conferir que a URL de autorização gerada
(`GET /api/v1/auth/sso/login/` → campo `authorize_url` → parâmetro `redirect_uri`)
bate com o que está cadastrado no client do Keycloak.

### 8.5 Bug #2 — `scope=groups` não existe no realm (`invalid_request` / `Invalid scopes`)

**Sintoma:** igual ao Bug #1 pro usuário (erra antes da tela de login) — só se
distingue pelo log.

**Log do Keycloak:**
```
ERROR [org.keycloak.services] KC-SERVICES0093: Invalid parameter value for: scope
WARN  [org.keycloak.events] type="LOGIN_ERROR" ... error="invalid_request"
      reason="Invalid scopes: openid email profile groups"
```

**Causa real:** o backend sempre pede `scope=openid email profile groups`
(`apps/accounts/oidc.py`, não configurável) porque a claim `groups` é como o JIT
provisioning decide quem autoriza. O Keycloak valida cada palavra de `scope` contra
os *client scopes* cadastrados no **realm** — se não existir nenhum client scope
literalmente chamado `groups`, a requisição inteira é rejeitada, mesmo que o client
já tenha um protocol mapper de grupo anexado diretamente a ele (mapper direto no
client não cria um scope "pedível" por nome).

**Correção — criar o client scope via `kcadm.sh`** (dentro do container do
Keycloak; ajustar `-r <realm>`):
```bash
kcadm.sh config credentials --server http://localhost:8080 --realm master \
  --user <admin> --password <senha>

cat > /tmp/groups-scope.json <<'EOF'
{
  "name": "groups",
  "protocol": "openid-connect",
  "attributes": { "display.on.consent.screen": "false", "include.in.token.scope": "true" },
  "protocolMappers": [{
    "name": "groups",
    "protocol": "openid-connect",
    "protocolMapper": "oidc-group-membership-mapper",
    "config": {
      "full.path": "false",
      "id.token.claim": "true",
      "access.token.claim": "true",
      "claim.name": "groups",
      "userinfo.token.claim": "true",
      "multivalued": "true"
    }
  }]
}
EOF

kcadm.sh create client-scopes -r <realm> -f /tmp/groups-scope.json -i
# guarde o id retornado

kcadm.sh update clients/<client-uuid>/optional-client-scopes/<scope-id> -r <realm>
```
Optional (não default) porque o backend já pede `groups` explicitamente no
`scope=` — não precisa forçar em todo token emitido pelo realm.

### 8.6 Bug #3 — grupo de autorização não existe (`sso_account_not_staff`)

**Sintoma:** login no Keycloak funciona (aceita usuário/senha), redireciona de
volta, e **a PaperMoon** (não mais o Keycloak) devolve 403.

**Log do Django:**
```
{"level": "WARNING", "logger": "django.request", "message": "Forbidden: /api/v1/auth/sso/callback/"}
```
Corpo da resposta: `{"code": "sso_account_not_staff", ...}`.

**Causa real:** `staff_group` apontava pra um grupo (`papermoon-staff`) que nunca
existiu na árvore de grupos do cliente — confirmado listando **todos** os grupos do
realm (`kcadm.sh get groups -r <realm> --fields name`) e não achando nenhuma
ocorrência, nem parecida.

**Correção — decisão de negócio, não técnica:** conversar com quem administra o AD
do cliente pra identificar **quais grupos já existentes** devem autorizar acesso
(nunca criar um grupo novo na estrutura organizacional deles pra isso). Nesse caso:
`Grupo Nucleo de TI`, `Grupo TI - Administradores`, `Grupo TI  - HelpDesk`,
`Administrators`, `Domain Admins`. Configurado como lista separada por vírgula em
`staff_group` (Backoffice → Configurações, ou direto via shell):

```python
from apps.accounts.models import SSOConfiguration
from apps.accounts.sso_config import invalidate_sso_config_cache

row = SSOConfiguration.get_solo()
row.staff_group = "Grupo Nucleo de TI,Grupo TI - Administradores,Grupo TI  - HelpDesk,Administrators,Domain Admins"
row.save(update_fields=["staff_group"])
invalidate_sso_config_cache()  # cache tem TTL de 30s, mas força refletir na hora
```

**Detalhe que custou tempo de debug:** um dos nomes reais do AD tem espaço
duplicado (`"Grupo TI  - HelpDesk"`) — visualmente idêntico ao que se digitaria no
backoffice, mas byte-a-byte diferente. Isso motivou reforçar `_normalize_group()`
(`apps/accounts/oidc.py`) pra colapsar espaços internos duplicados além de
case/barra inicial — sem isso, esse grupo específico nunca bateria mesmo estando
"certo" a olho nu. Ao configurar um novo `staff_group`, **copiar o nome exato** de
`kcadm.sh get groups` em vez de digitar de memória.

### 8.7 Checklist pra replicar em outro cliente/integrador

1. Confirmar o domínio público real do frontend (`getent hosts` + `curl -I`, nunca
   assumir) e alinhar `FRONTEND_URL`/`NEXT_PUBLIC_SITE_URL`/`CORS_ALLOWED_ORIGINS`.
2. Cadastrar o client no Keycloak com o `redirect_uri` **desse** domínio confirmado.
3. Garantir que existe um client scope `groups` no realm, associado ao client
   (seção 8.5) — sem isso a claim de grupos nunca chega, mesmo com mapper direto.
4. Listar os grupos reais do realm (`kcadm.sh get groups`) e decidir, com quem
   administra aquele AD/Keycloak, quais grupos já existentes autorizam staff —
   nunca criar grupo novo na organização de outra empresa pra isso.
5. Configurar `staff_group` como lista separada por vírgula com os nomes **exatos**
   (copiados, não digitados).
6. Testar de ponta a ponta com um usuário real de cada grupo configurado — e com um
   usuário de fora de todos eles, pra confirmar que o 403 ainda dispara quando
   deveria.

---

## 9. Referências

- ADR de decisão original: `docs/adrs/0002-sso-keycloak-staff.md`
- ADR do roadmap mais amplo (OTel, feature flags, Terraform, gRPC): `docs/adrs/0003-portfolio-tech-expansion.md`
- Referência de API: `docs/backend/api.md` (seções "Auth" e "Admin — SSO")
- Roadmap: `CLAUDE.md`, Fase 5
- Testes: `backend/tests/unit/test_accounts_oidc.py` (classe `TestGroupAuthorizesStaff`
  cobre a lista separada por vírgula e a normalização de espaço duplicado)
