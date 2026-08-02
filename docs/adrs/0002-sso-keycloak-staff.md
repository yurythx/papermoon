# ADR 0002: SSO via Keycloak para acesso de staff (backoffice)

## Status

Accepted

## Contexto

A PaperMoon passou a operar uma instância de Keycloak na rede interna. Hoje, todo login
— tanto de clientes (tenants) quanto de staff (`is_staff=True`) — passa pelo mesmo fluxo
de email/senha contra `Simple JWT` (RS256), implementado em `apps/accounts/views.py`.

Já existe um `KeycloakProvisioner` (`apps/provisioning/keycloak.py`), mas ele resolve um
problema diferente: cria realms Keycloak **para clientes**, como um dos produtos/serviços
provisionáveis da plataforma. Não deve ser reaproveitado para autenticação da própria
PaperMoon — são domínios de responsabilidade distintos.

Motivação para SSO de staff:

- Centralizar autenticação de equipe interna em um único IdP corporativo (Keycloak já é
  fonte de verdade para outros sistemas internos na rede).
- Reduzir superfície de senhas — staff deixa de ter uma senha adicional só para o backoffice.
- Ganho de portfólio: integração OIDC real, não um toy example.

## Decisão

Keycloak atua como Identity Provider **apenas para login de staff**, via OIDC Authorization
Code + PKCE. O login por email/senha **continua existindo** para todos os usuários
(clientes e staff) — SSO é um método adicional, não uma substituição. Login de clientes
(tenants) não é afetado por esta decisão.

A PaperMoon continua sendo a única emissora de sessão: o backend troca o `code` do Keycloak
no callback, valida o `id_token` (issuer, audience, nonce, assinatura via JWKS do Keycloak) e,
se o e-mail corresponder a um `CustomUser` com `is_staff=True`, emite o par de tokens
RS256 de sempre via Simple JWT. Nenhum código downstream (cookies BFF, blacklist, throttle,
`IsActiveCustomer`) muda.

### Por que não validar tokens do Keycloak diretamente em cada request

Trocar `JWTAuthentication` por validação direta de tokens do Keycloak quebraria rotação de
refresh token, blacklist e rate limiting que já funcionam. Também acoplaria a disponibilidade
da API à disponibilidade do Keycloak em todo request autenticado — inaceitável para clientes,
que nem usam Keycloak. Delegar a emissão da sessão para o Keycloak e re-emitir localmente
mantém o Keycloak como dependência apenas no momento do login de staff.

### Por que não usar `mozilla-django-oidc` ou lib equivalente

Essas libs assumem sessão Django (cookies de sessão do próprio Django), não o par
BFF (Next.js) + JWT stateless que a PaperMoon usa. Um cliente OIDC fino, escrito à mão
(troca de código + validação de JWKS com `cryptography`, já uma dependência existente),
é mais simples de auditar e não briga com a arquitetura atual.

## Desenho técnico

A primeira versão desta ADR descrevia o Keycloak redirecionando ora para um endpoint
Django, ora para uma rota Next.js, sem decidir qual URL é de fato registrada como
`redirect_uri` no client do Keycloak. Corrigido abaixo: **só a rota Next.js é pública o
suficiente para ser o `redirect_uri`; o Django nunca é alcançado diretamente pelo
browser neste fluxo** — mantém o invariante do README de que o BFF centraliza auth.

Passo a passo:

1. Browser abre `GET /api/auth/sso/` (Next.js).
2. Next.js faz `fetch` server-to-server para `GET {DJANGO_INTERNAL_URL}/auth/sso/login/`,
   que responde **200 JSON** `{authorize_url}` (URL de authorize do Keycloak, já com
   `state`/PKCE `code_challenge`/`nonce` gerados e persistidos pelo Django) — não um
   302 de verdade, porque quem lê essa resposta é o `fetch` do Next.js rodando
   server-side, e o modo `redirect: "manual"` do Fetch API filtra os headers de uma
   resposta de redirect (`opaqueredirect`), tornando o `Location` ilegível em vários
   runtimes. JSON evita essa armadilha. Next.js então responde ao browser com
   `NextResponse.redirect(authorize_url)`.
3. Browser é redirecionado ao Keycloak, autentica, e o Keycloak redireciona de volta
   para o `redirect_uri` registrado no client — que é
   `https://app.papermoon.cloud/api/auth/sso/callback` (rota Next.js), com
   `?code=...&state=...`.
4. `app/api/auth/sso/callback/route.ts` recebe `code`/`state` e faz
   `POST {DJANGO_INTERNAL_URL}/auth/sso/callback/` server-to-server, repassando ambos.
5. Django troca o `code` pelos tokens do Keycloak (usa o `client_secret`, nunca exposto
   ao browser), valida o `id_token`, localiza o `CustomUser`, emite o JWT RS256 de
   sempre e responde `{access, refresh}`.
6. Next.js aplica `applyAuthCookies` (mesma função de `lib/session.ts` usada por
   `/api/auth/login`) e redireciona para `/backoffice`.

### Backend (`apps/accounts/`)

- Novo módulo `oidc.py`: discovery do Keycloak, geração de `state`/`nonce`/PKCE
  `code_verifier`, troca de `code` por tokens, validação de `id_token` via JWKS
  (`PyJWT`'s `PyJWKClient`, que já cacheia as chaves).
- `state` é a chave de um registro em `cache` (Redis, mesmo backend usado por
  `LoginAttemptGuard`) contendo `{code_verifier, nonce}`, TTL 5 min, **apagado no
  primeiro uso** (`cache.get` + `cache.delete` juntos) — um `state` não pode ser
  resgatado duas vezes.
- Endpoints, mesmo padrão dos existentes (`AllowAny`, throttle dedicado `scope="sso"`):
  - `GET /api/v1/auth/sso/login/` — gera state/PKCE/nonce, devolve `200 {authorize_url}`.
    Só é chamado server-to-server pelo Next.js (ver nota acima sobre por que não é
    um 302 de verdade).
  - `POST /api/v1/auth/sso/callback/` — recebe `{code, state}` (não é a rota que o
    Keycloak acessa — é a rota que o Next.js chama depois de receber o redirect).
    Troca o código, valida claims, localiza `CustomUser` por e-mail. **Não faz JIT
    provisioning automático de conta nova** — se o e-mail não existir como
    `is_staff=True`, retorna `403 sso_account_not_staff`. Isso evita escalada de
    privilégio via um client Keycloak mal configurado.
  - Em caso de sucesso, retorna `{access, refresh}` no mesmo formato do `LoginView`.
- Novas settings, namespace **separado** do provisioner existente para não colidir
  com `KEYCLOAK_API_URL`/`KEYCLOAK_ADMIN_TOKEN`:
  ```
  KEYCLOAK_SSO_ISSUER=https://keycloak.internal/realms/papermoon-staff
  KEYCLOAK_SSO_CLIENT_ID=papermoon-backoffice
  KEYCLOAK_SSO_CLIENT_SECRET=...
  KEYCLOAK_SSO_REDIRECT_URI=https://app.papermoon.cloud/api/auth/sso/callback
  ```

### Frontend (BFF)

- `app/api/auth/sso/route.ts` — resolve o `Location` do Django e redireciona o browser
  (passo 2 acima). Não gera nem guarda state — isso é responsabilidade exclusiva do
  Django, que tem acesso ao Redis e ao `client_secret`.
- `app/api/auth/sso/callback/route.ts` — recebe `code`/`state` do Keycloak, repassa ao
  Django, aplica `applyAuthCookies` e redireciona para `/backoffice` (passos 4-6 acima).
  Em caso de erro do Django, redireciona para `/login?error=sso_failed`.
- Botão "Entrar com Keycloak" em `/login`, visível apenas quando
  `NEXT_PUBLIC_SSO_ENABLED=true` (permite desligar sem deploy se o Keycloak cair).

### Segurança

- PKCE obrigatório (mesmo sendo confidential client) — defesa em profundidade.
- Validar `iss`, `aud`, `exp`, `nonce` — rejeitar qualquer id_token sem os quatro.
- Callback tem rate throttle próprio (mesmo padrão de `LoginRateThrottle`).
- Sem fallback silencioso: falha de validação = 403 explícito, nunca criação implícita de sessão.

## Consequências

### Positivas

- Staff ganha SSO sem tocar no fluxo de autenticação de clientes.
- Zero mudança em `IsActiveCustomer`, cookies BFF, licensing — raio de explosão pequeno.
- Caminho de rollback trivial: `NEXT_PUBLIC_SSO_ENABLED=false` desliga o botão sem remover código.

### Negativas / trade-offs

- Dois caminhos de login para manter (senha + SSO) — mais superfície de teste.
- Dependência do Keycloak estar acessível pela rede onde a API roda (rede interna) —
  aceitável porque o escopo é staff, que já está nessa rede.

## Não incluído nesta decisão

- SSO para clientes/tenants (exigiria realm por tenant e mapeamento de role via claims —
  ver `apps/provisioning/keycloak.py` como base se isso virar requisito real de produto).
- Remoção do login por senha.

## Atualização — configuração passou de env var para runtime (DB + backoffice)

O desenho original desta ADR (seções acima) descrevia `KEYCLOAK_SSO_*` como variáveis
de ambiente e `NEXT_PUBLIC_SSO_ENABLED` como flag de build — exigia redeploy pra
ativar/desativar o SSO ou trocar credenciais. Isso foi substituído: a configuração
(`enabled`/`issuer`/`client_id`/`client_secret`) agora vive em `SSOConfiguration`
(banco, singleton, `client_secret` criptografado com Fernet) e é editável em runtime
em **Backoffice → Configurações**, sem deploy.

As decisões de arquitetura desta ADR (Keycloak como IdP só pra staff, PaperMoon
continua emissora do JWT, sem JIT provisioning, PKCE, coexistência com login por
senha) **continuam todas válidas** — só a *fonte* da configuração mudou, não o fluxo
OIDC em si. Detalhes completos da implementação atual, passo a passo de configuração e
troubleshooting: `docs/backend/sso-keycloak-integration.md`.
