/**
 * Fonte única da verdade sobre quais serviços estão disponíveis publicamente
 * (Product.is_active no backend, já usado pelo toggle da página Produtos e
 * do editor CMS). Todo lugar do site que "anuncia" um serviço — home,
 * listagem, página individual (via middleware), dropdown do contato —
 * consulta isto antes de renderizar, em vez de assumir que um slug
 * hardcoded ainda está disponível.
 *
 * Usa /products/active-slugs/ (sem throttle), não /products/catalog/ — o
 * catalog tem AnonRateThrottle padrão (200/dia) porque é feito pra consumo
 * externo real; isto aqui é chamado a cada request de página de serviço
 * (inclusive pelo middleware), o mesmo tráfego servidor-a-servidor que
 * justificou tirar o throttle do health check. Confirmado ao vivo: usar o
 * catalog aqui estourava a cota em minutos de teste.
 *
 * Retorna `null` (não um Set vazio) quando o Django está inalcançável — os
 * chamadores devem tratar `null` como "não filtrar" (fail-open: mostra tudo).
 * Um Set vazio de verdade (Django respondeu, catálogo genuinamente vazio) é
 * uma resposta válida e differente de falha; só null significa "não sei".
 */

const DJANGO_URL = process.env.DJANGO_INTERNAL_URL ?? "http://localhost:8000/api/v1";

export async function fetchActiveServiceSlugs(): Promise<Set<string> | null> {
  try {
    const res = await fetch(`${DJANGO_URL}/products/active-slugs/`, {
      // Mesma janela do resto do conteúdo de /servicos — não precisa ser
      // mais fresco que isso, e cache indefinido esconderia um "desativar"
      // por tempo demais.
      next: { revalidate: 60, tags: ["active-services"] },
    });
    if (!res.ok) return null;
    const json = await res.json();
    const slugs: string[] = json?.data ?? json ?? [];
    if (!Array.isArray(slugs)) return null;
    return new Set(slugs);
  } catch {
    return null;
  }
}

/** true se o slug deve ser exibido — desconhecido (fetch falhou) sempre exibe. */
export function isServiceVisible(slug: string, activeSlugs: Set<string> | null): boolean {
  return activeSlugs === null || activeSlugs.has(slug);
}
