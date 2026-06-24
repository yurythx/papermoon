# PaperMoon Frontend — Padrões de Desenvolvimento

Padrões recorrentes adotados no frontend. Siga-os ao adicionar novas rotas ou componentes.

---

## 1. Estrutura de uma página autenticada

Toda página dentro de `/dashboard` ou `/backoffice` segue este padrão:

```
app/dashboard/minha-rota/
├── page.tsx          ← Client component com lógica da página
├── loading.tsx       ← Skeleton que espelha o shape da página
└── error.tsx         ← (opcional) se a rota tiver tratamento específico
```

`error.tsx` e `loading.tsx` no nível do layout (`dashboard/` e `backoffice/`) capturam todas as sub-rotas. Adicione um arquivo local apenas se precisar de comportamento diferenciado.

---

## 2. Padrão de fetch com TanStack Query

```tsx
// ✅ Correto — useQuery com queryFn tipada
const { data, isLoading } = useQuery({
  queryKey: ["licenses"],
  queryFn: licenseService.list,
  enabled: !!me?.customer,
});

// ✅ Mutação com invalidação
const mutation = useMutation({
  mutationFn: licenseService.revoke,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ["licenses"] }),
});

// ❌ Errado — fetch direto sem cache
const [data, setData] = useState(null);
useEffect(() => { fetch(...).then(setData); }, []);
```

### QueryKeys

- Use arrays: `["licenses"]`, `["license", id]`, `["invoices", { status }]`
- Globais (sem filtro): array de um elemento
- Com parâmetros: array com objeto no segundo elemento
- Invalidação ampla: `queryClient.invalidateQueries({ queryKey: ["licenses"] })` invalida todas as queries com prefixo `"licenses"`

---

## 3. Serviços e BFF

Toda chamada HTTP passa por `src/lib/services.ts`, que abstrai o Axios com tipagem completa:

```ts
// services.ts
export const licenseService = {
  list: () => api.get<ApiResponse<PaginatedResponse<License>>>("/proxy/client/licenses/").then(unwrap),
  get:  (id: string) => api.get<ApiResponse<License>>(`/proxy/client/licenses/${id}/`).then(unwrap),
};
```

`unwrap()` extrai `.data` e lança erro se `success: false`. As páginas consomem apenas o dado final — sem tratar o envelope `{ success, data, error }` manualmente.

**Nunca chamar o Django diretamente.** Toda chamada vai para `/api/...` (BFF Next.js).

---

## 4. Estado global — Zustand

Apenas dois stores globais:

```ts
// store/auth.ts
const { me, setMe, clearMe } = useAuthStore();

// store/sidebar.ts
const { isOpen, toggle, mobileOpen, toggleMobile } = useSidebarStore();
```

**Não adicionar estado global** para dados do servidor (use TanStack Query) nem para estado de UI local (use `useState`). Zustand só para estado que precisa ser compartilhado entre layouts distintos (auth) ou componentes separados na árvore (sidebar).

---

## 5. Componentes — quando memoizar

```tsx
// ✅ Memoize quando o componente:
// - recebe callbacks do pai (useCallback no pai também)
// - é renderizado em listas longas
// - faz trabalho pesado (cálculos, queries)
const ServiceCard = memo(function ServiceCard({ service }: Props) { ... });

// ✅ Props primitivas para memo funcionar bem
// Errado — novo objeto a cada render quebra memo:
<NavLink badge={{ label: "3", variant: "warning" }} />
// Correto — primitivos comparados por valor:
<NavLink badgeLabel="3" badgeVariant="warning" />

// ✅ Constantes em nível de módulo (fora do componente)
const STATUS_CLASSES = { active: "text-success", ... } as const;
function MyComponent() { /* usa STATUS_CLASSES */ }
```

---

## 6. SVG com gradientes — idSuffix

Múltiplos `<RissenMark>` na mesma página criam conflito de `id` SVG se usarem o mesmo gradiente. Sempre passe um sufixo único:

```tsx
<RissenMark idSuffix="topbar" glow />       // topbar
<RissenMark idSuffix="nav" />               // landing nav
<RissenMark idSuffix="footer" size={24} />  // landing footer
<RissenMark idSuffix="auth-left" glow />    // painel de auth
```

A mesma regra se aplica a qualquer SVG com `<defs>` compartilhadas.

---

## 7. Páginas de autenticação — layout split-screen

Todas as páginas auth (`/login`, `/forgot-password`, `/reset-password`, `/onboarding`) seguem o mesmo layout:

```
┌─────────────────────────────┬──────────────────────┐
│  Painel escuro 44%          │  Formulário flex-1   │
│  bg-[#080811]               │                      │
│  RissenMark + tagline       │  Logo mobile (lg:hidden) │
│  Feature list               │  Heading + form      │
│  Social proof / steps       │  Links secundários   │
│  Copyright                  │                      │
└─────────────────────────────┴──────────────────────┘
       lg:flex (hidden em mobile)        sempre visível
```

O painel esquerdo usa `hidden lg:flex` — em mobile só o formulário aparece, com o logo no topo.

---

## 8. Padrão de resposta de erro

```tsx
// Handler de erro em mutations/forms
} catch (err) {
  if (axios.isAxiosError(err)) {
    const msg = err.response?.data?.error?.message
              ?? err.response?.data?.detail
              ?? err.message;
    setError(msg ?? "Erro inesperado.");
  } else {
    setError("Erro inesperado. Tente novamente.");
  }
}
```

Sempre acesse `err.response?.data?.error?.message` primeiro — esse é o campo do envelope `UnifiedResponseRenderer` do Django. O `data?.detail` é fallback para exceções DRF não interceptadas.

---

## 9. Acessibilidade

- Todo `<input>` deve ter `<label htmlFor={id}>` com `id` correspondente.
- Botões de ação que só têm ícone devem ter `aria-label`.
- Modais e dialogs devem ter `role="dialog"` e `aria-labelledby`.
- `StatusBadge` e chips informativos usam `role="status"` implicitamente via semântica — não adicionar `aria-live` desnecessariamente.

---

## 10. Testes — onde colocar o quê

| Tipo | Onde | O que testar |
|---|---|---|
| Integração de componente | `src/__tests__/integration/` | Renderização + interação + estados (loading, vazio, erro) usando MSW |
| Unitário de função pura | `src/__tests__/unit/` | services.ts, utils.ts |
| E2E | `e2e/` | Golden paths com backend real + seed data |

**Nunca mockar o módulo inteiro** de um componente filho em testes de integração — teste o comportamento visível, não a implementação interna.

```ts
// ✅ Teste o que o usuário vê
expect(screen.getByText("Plano Starter")).toBeInTheDocument();

// ❌ Não testar estado interno
expect(component.state.isLoading).toBe(false);
```

---

## 11. Skeleton loading

Todo `loading.tsx` deve espelhar o shape da página para evitar layout shift (CLS):

```tsx
// ✅ Shape fiel
export default function LicensesLoading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-40 rounded" />        {/* título */}
      {[1, 2, 3].map(i => <Skeleton key={i} className="h-28 rounded-xl" />)} {/* cards */}
    </div>
  );
}

// ❌ Genérico — não comunica o que vai aparecer
export default function Loading() {
  return <Spinner />;
}
```

Exceção: `app/loading.tsx` (root) usa `<Spinner>` pois o layout ainda não carregou.
