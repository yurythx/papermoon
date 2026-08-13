# Arquitetura do Frontend — PaperMoon

## Visão Geral

Aplicação Next.js 14 com App Router. Toda comunicação com o Django passa por um BFF (Backend-for-Frontend) em `/app/api/`, que mantém tokens JWT em cookies httpOnly — sem exposição ao JavaScript do browser.

## Stack

| Camada | Tecnologia |
|---|---|
| Framework | Next.js 14.2 (App Router) |
| Linguagem | TypeScript strict |
| Estilização | Tailwind CSS (tema customizado com tokens semânticos) |
| Estado servidor | TanStack Query v5 (react-query) |
| Estado global | Zustand (auth + sidebar) |
| HTTP | Axios (chamadas ao BFF `/api/...`) |
| Toasts | Sonner |
| Ícones | Lucide React |
| Monitoramento | Sentry (`@sentry/nextjs`) |
| Testes unitários | Vitest + Testing Library + MSW |
| E2E | Playwright |

## Estrutura de Pastas

```
frontend/src/
├── app/                          # Next.js App Router pages
│   ├── layout.tsx                # Root layout (fontes, providers, Sentry)
│   ├── loading.tsx               # Spinner global de carregamento
│   ├── not-found.tsx             # Página 404 customizada
│   ├── error.tsx                 # Error boundary global (reporta ao Sentry)
│   ├── page.tsx                  # Landing page pública
│   ├── servicos/                 # Grid de todos os serviços + [slug]/ (detalhe SEO/marketing)
│   ├── blog/                     # Lista pública de posts + [slug]/ (detalhe, nunca mostra draft)
│   ├── sobre/                    # Página institucional
│   ├── termos/                   # Termos de uso (página estática pública)
│   ├── register/                 # Auto-cadastro público (cria CustomUser sem Customer)
│   │
│   ├── login/                    # Formulario JWT com identidade visual da plataforma
│   ├── forgot-password/          # Solicitar reset de senha
│   ├── reset-password/           # Confirmar reset via uid+token
│   ├── onboarding/               # Usuário autenticado sem customer vinculado
│   ├── invite/
│   │   └── accept/               # Aceitar convite + criar senha
│   │
│   ├── dashboard/                # Área autenticada do cliente
│   │   ├── layout.tsx            # Topbar + Sidebar + banners de status
│   │   ├── page.tsx              # Hero + KPIs + Meus Serviços + alertas
│   │   ├── licenses/             # Lista de licenças + detalhe [id]
│   │   ├── subscriptions/        # Assinaturas (reativar / cancelar)
│   │   ├── invoices/             # Faturas com filtros + export CSV
│   │   ├── catalog/              # Catálogo de produtos (ativar plano)
│   │   ├── api-keys/             # Gerenciar API Keys + quota
│   │   ├── team/                 # Membros da equipe + convites
│   │   ├── notifications/        # Histórico de notificações
│   │   └── profile/              # Dados cadastrais + alterar senha
│   │
│   ├── backoffice/               # Área admin interna (is_staff=True)
│   │   ├── layout.tsx            # Layout + guard is_staff
│   │   ├── page.tsx              # MRR/ARR + API usage dashboard
│   │   ├── customers/            # CRUD de clientes (suspend/reactivate/cancel/delete)
│   │   ├── invoices/             # Todas as faturas (soft-delete)
│   │   ├── subscriptions/        # Admin de assinaturas (suspend/cancel/renew)
│   │   ├── products/             # Produtos + pricings (criar/editar/toggle)
│   │   ├── cms/                  # Editor de páginas de serviço + upload de imagens WebP
│   │   ├── blog/                 # CRUD de posts (draft/publish) + [id]/ (editor Markdown)
│   │   ├── feature-flags/        # CRUD de flags (global ou por customer)
│   │   ├── integrations/keycloak/# Ferramentas de suporte: validador + gerador manual de campos
│   │   ├── health/               # Status de DB/Redis/Celery em tempo real
│   │   ├── settings/             # Config runtime do SSO Keycloak (issuer/client/teste de conexão)
│   │   └── audit/                # Audit trail com filtros
│   │
│   └── api/                      # BFF — Next.js Route Handlers
│       ├── auth/                 # login, logout, me, change-password, password-reset
│       ├── invitations/          # accept (sem auth, vai direto ao Django)
│       └── proxy/[...path]/      # Catch-all: proxy autenticado → Django API
│                                   # (transparently refreshes JWT on 401)
│
├── components/
│   ├── common/
│   │   ├── papermoon-mark.tsx    # SVG principal da marca PaperMoon
│   │   └── rissen-mark.tsx       # Alias de compatibilidade que reexporta papermoon-mark
│   ├── ui/                       # Design system primitivo
│   │   ├── badge.tsx             # Variants: success/warning/danger/info/muted/accent
│   │   ├── button.tsx            # Variants + loading spinner
│   │   ├── input.tsx
│   │   ├── skeleton.tsx
│   │   ├── spinner.tsx
│   │   └── ...
│   ├── compound/                 # Compostos com lógica de domínio
│   │   ├── status-badge.tsx      # Badge semântico: active/suspended/paid/overdue/...
│   │   ├── time-progress.tsx     # Barra de progresso de validade de licença
│   │   ├── page-header.tsx       # Header de página com título, descrição e actions
│   │   └── empty-state.tsx       # Estado vazio com ícone, título e CTA opcional
│   ├── layout/
│   │   ├── topbar.tsx            # Logo + NotificationBellMenu + user menu
│   │   ├── sidebar.tsx           # NavLink + collapse + mobile drawer
│   │   └── dashboard-shell.tsx   # Guard auth + SuspendedBanner + CancelledBanner
│   ├── backoffice/               # Modais e cards do backoffice
│   │   ├── product-card.tsx
│   │   ├── product-form-modal.tsx
│   │   └── pricing-manager-modal.tsx
│   └── marketing/
│       └── nav.tsx               # Navbar da landing page
│
├── hooks/
│   └── useAuth.ts                # useAuth() — lê me do AuthStore
├── lib/
│   ├── api.ts                    # Axios instance com base URL → /api/...
│   ├── services.ts               # Todas as chamadas ao BFF (tipadas, com unwrap)
│   ├── services-content.ts       # Conteúdo estático de cada serviço (hero, features, FAQ)
│   ├── merge-service.ts          # Mescla services-content.ts (estático) com CMS (apps/cms)
│   ├── active-services.ts        # Fail-open: quais slugs de serviço aparecem no nav/grid
│   ├── blog.ts                   # fetchBlogPosts()/fetchBlogPost() — consome /api/v1/blog/
│   ├── cms.ts                    # Fetch de ServicePage do CMS
│   ├── faq-content.ts            # Conteúdo estático do FAQ da home
│   ├── session.ts                # Leitura de cookies httpOnly no BFF (route handlers)
│   └── utils.ts                  # cn(), formatters, slugify()
├── store/
│   ├── auth.ts                   # Zustand: { me, setMe, clearMe }
│   └── sidebar.ts                # Zustand: { isOpen, toggle, mobileOpen, toggleMobile }
└── types/
    └── index.ts                  # Interfaces TypeScript de todos os modelos da API
```

## Fluxo de Autenticação

```
Browser
  │  POST /api/auth/login { email, password }
  ▼
BFF (Next.js Route Handler)
  │  POST http://django-api:8000/api/v1/auth/login/
  ▼
Django
  │  { access, refresh }
  ▼
BFF seta cookies httpOnly:
- papermoon_access  (Max-Age: 3600)
- papermoon_refresh (Max-Age: 604800)
  │  { message: "Login realizado." }
  ▼
Browser (sem acesso JS aos tokens)
  │  GET /api/proxy/client/me/
  ▼
BFF lê cookie papermoon_access → Authorization: Bearer <access>
  │  GET http://django-api:8000/api/v1/auth/me/
  ▼
Django → { user, customer, role }
```

O BFF realiza refresh transparente: se o Django retorna 401, o BFF tenta renovar com `papermoon_refresh` e repete a requisicao original sem que o browser perceba.

> Os cookies do BFF agora seguem o prefixo `papermoon_*`. Em ambientes ja autenticados, a troca exige invalidacao controlada de sessao ou uma janela de compatibilidade para evitar logout inesperado.

### SSO (Keycloak) — só para staff

`/login` mostra um botão extra "Entrar com Keycloak" quando `GET /api/auth/sso/status/` reporta
habilitado. Fluxo: `GET /api/auth/sso/login/` (BFF → Django, gera `authorize_url` com PKCE/state) →
browser navega direto pro Keycloak → volta com `code`/`state` → BFF chama
`POST /api/auth/sso/callback/`, que troca pelo par de tokens `papermoon_*` do jeito de sempre. Só
autentica contas `is_staff=True` (JIT provisiona na primeira vez, se o grupo do AD autorizar) — ver
`docs/backend/sso-keycloak-integration.md`.

## Proxy Catch-All

`/app/api/proxy/[...path]/route.ts` — proxy transparente que:
- Suporta todos os métodos HTTP (GET, POST, PATCH, PUT, DELETE)
- Injeta `Authorization: Bearer` em toda chamada ao Django
- Renova tokens silenciosamente (401 → refresh → retry)
- Passa binários (CSV export) com `Content-Type` e `Content-Disposition` originais

## Fluxo de Dados (TanStack Query)

- Toda a app é Client-Side Rendering via layouts + client components
- `useQuery` / `useMutation` chamam funções de `services.ts`
- Invalidação via `queryClient.invalidateQueries()` após mutações
- `NotificationBellMenu` refetch a cada 30s (polling leve)

## Design System

- Tokens oficiais de marca: `--papermoon-bg`, `--papermoon-primary`, `--papermoon-accent`, `--papermoon-secondary`
- Aliases semanticos preservados para compatibilidade: `--surface-*`, `--text-*`, `--border-*`
- Tailwind custom tokens: `bg-surface-0`, `text-text-primary`, `border-border-subtle`
- Estados visuais globais de foco e selecao consomem tokens, sem cores hard-coded
- Tipografia: Inter (sans) + JetBrains Mono (mono)
- Tema com `light` e `dark` mode via `next-themes`, com base pronta para evolucao com `prefers-color-scheme`

## Performance

- `React.memo` em subcomponentes pesados (`ServiceCard`, `StatusCard`, `AlertCard`, `NavLink`)
- Constantes em nível de módulo para evitar recriação a cada render
- Modais extraídos como componentes separados: `ProductFormModal`, `PricingManagerModal`
- `PaperMoonMark` permanece memoizado com `idSuffix`; `rissen-mark.tsx` ficou apenas como alias de compatibilidade temporaria
- `staleTime` configurado por query (ex: 30s para listas admin, 60s para quota)

## Responsividade

- Sidebar: drawer móvel com overlay em `< md`; colapsa para 64px em desktop
- Topbar: `handleMenuToggle()` detecta largura para chamar `toggleMobile()` vs `toggle()`
- Tabelas admin: `overflow-x-auto` + `min-w-[px]` em todas as 6 tabelas
- Auth pages: painel branding `hidden lg:flex` — só desktop vê split-screen

## Testes

| Tipo | Ferramenta | Quantidade |
|---|---|---|
| Unitário + Integração | Vitest + Testing Library + MSW | ~256 testes em 28 arquivos |
| E2E | Playwright | 19 specs |

- Mocks em `src/__tests__/mocks/handlers.ts` — MSW intercepta chamadas ao BFF
- E2E requerem frontend + backend rodando com seed data (`make seed`)
