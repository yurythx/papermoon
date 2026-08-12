import { test, expect, type Page } from "@playwright/test";

/**
 * Fluxo completo do blog, do backoffice ao público: criar rascunho, escrever
 * o corpo com a toolbar de Markdown, publicar, conferir a página pública +
 * listagem + RSS, e por fim excluir e confirmar o 404.
 *
 * Não depende de seed — `make seed` não popula posts de blog (ver
 * backend/apps/blog), então o teste cria e limpa os próprios dados (mesmo
 * padrão de team.spec.ts com `e2e-${Date.now()}`). Roda como admin
 * (storageState .auth/admin.json via o prefixo "backoffice" no nome do
 * arquivo) porque criar/editar/excluir posts exige IsAdminUser.
 *
 * As páginas públicas (`/blog`, `/blog/rss.xml`) são cacheadas por ISR com
 * `revalidate: 60` e tag compartilhada `blog-posts` (frontend/src/lib/blog.ts).
 * O save do post dispara revalidação on-demand via Celery (apps/blog/tasks.py
 * → POST /api/revalidate), mas isso depende do worker estar rodando — sem
 * ele, o teste ainda passa esperando a janela passiva de 60s. `/blog/<slug>`
 * em si usa uma tag própria (`blog-post-<slug>`) e nunca foi visitada antes
 * (slug único por execução), então essa página sempre é um cache-miss e
 * reflete o conteúdo publicado imediatamente — só a listagem e o RSS
 * precisam do poll de tolerância.
 */

const RUN_ID = Date.now();
const SLUG = `e2e-post-${RUN_ID}`;
const TITLE = `Post de teste E2E ${RUN_ID}`;

/** Repete um `check` até ele não lançar, recarregando a página a cada tentativa
 * (o cache do Next é no servidor — só um novo `goto` força um novo fetch). */
async function pollUntil(page: Page, url: string, check: () => Promise<void>, timeoutMs = 65_000) {
  const start = Date.now();
  let lastError: unknown;
  while (Date.now() - start < timeoutMs) {
    await page.goto(url, { waitUntil: "domcontentloaded" });
    try {
      await check();
      return;
    } catch (err) {
      lastError = err;
      await page.waitForTimeout(3000);
    }
  }
  throw lastError;
}

test.describe.serial("Blog — fluxo completo (criar → publicar → público → excluir)", () => {
  let postId: string;

  test("cria post como rascunho a partir da listagem do backoffice", async ({ page }) => {
    await page.goto("/backoffice/blog");
    await expect(page.getByRole("heading", { name: "Blog" })).toBeVisible({ timeout: 5000 });

    await page.getByRole("button", { name: /novo post/i }).first().click();
    await page.locator("#bp-title").fill(TITLE);
    await page.locator("#bp-slug").fill(SLUG); // sobrescreve o auto-slug pro valor único do teste
    await page.locator("#bp-excerpt").fill("Resumo gerado pelo teste E2E do blog.");
    await page.getByRole("button", { name: /criar post/i }).click();

    // onSuccess navega via window.location.href — reload completo, não client-side routing.
    await expect(page).toHaveURL(/\/backoffice\/blog\/.+/, { timeout: 15_000 });
    postId = page.url().split("/").pop()!;
    await expect(page.getByText("Rascunho").first()).toBeVisible({ timeout: 5000 });
  });

  test("escreve o corpo com a toolbar de Markdown e salva", async ({ page }) => {
    await page.goto(`/backoffice/blog/${postId}`);
    const bodyField = page.locator("textarea.font-mono");
    await expect(bodyField).toBeVisible({ timeout: 5000 });

    await bodyField.fill("Testando negrito");
    await bodyField.selectText();
    await page.getByTitle("Negrito").click();
    await expect(bodyField).toHaveValue("**Testando negrito**");

    const finalBody = [
      "Este post foi criado automaticamente pelo teste E2E do blog.",
      "",
      "## Seção de exemplo",
      "",
      "- Primeiro item",
      "- Segundo item",
      "",
      "Parágrafo final com **texto em negrito** de verdade.",
    ].join("\n");
    await bodyField.fill(finalBody);

    await page.getByRole("button", { name: /^salvar$/i }).click();
    await expect(page.getByText(/post salvo/i)).toBeVisible({ timeout: 8000 });
  });

  test("publica o post e confere o banner de status", async ({ page }) => {
    await page.goto(`/backoffice/blog/${postId}`);
    await expect(page.getByText("Rascunho").first()).toBeVisible({ timeout: 5000 });

    await page.getByRole("button", { name: /^publicar$/i }).click();
    await expect(page.getByText(/post salvo/i)).toBeVisible({ timeout: 8000 });
    await expect(page.getByText("Publicado").first()).toBeVisible();
    await expect(page.getByText(/visível em/i)).toBeVisible();
  });

  test("página pública do post renderiza título, corpo e tempo de leitura", async ({ page }) => {
    await page.goto(`/blog/${SLUG}`);
    await expect(page.getByRole("heading", { level: 1, name: TITLE })).toBeVisible({ timeout: 8000 });
    await expect(page.getByText(/min de leitura/i)).toBeVisible();
    await expect(page.getByText("Seção de exemplo")).toBeVisible();
    await expect(page.getByText("Primeiro item")).toBeVisible();
  });

  test("post aparece na listagem pública do blog", async ({ page }) => {
    test.setTimeout(90_000);
    await pollUntil(page, "/blog", async () => {
      await expect(page.getByText(TITLE)).toBeVisible({ timeout: 2000 });
    });
  });

  test("feed RSS inclui o post publicado", async ({ page }) => {
    test.setTimeout(90_000);
    const start = Date.now();
    let body = "";
    while (Date.now() - start < 65_000) {
      const res = await page.request.get("/blog/rss.xml");
      expect(res.ok()).toBeTruthy();
      body = await res.text();
      if (body.includes(SLUG)) break;
      await page.waitForTimeout(3000);
    }
    expect(body).toContain(SLUG);
    expect(body).toContain(TITLE);
  });

  test("exclui o post e confirma a remoção", async ({ page }) => {
    await page.goto(`/backoffice/blog/${postId}`);

    await page.getByRole("button", { name: /^excluir$/i }).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog.getByRole("heading", { name: /excluir post/i })).toBeVisible({ timeout: 5000 });
    await dialog.getByRole("button", { name: /^excluir$/i }).click();

    await expect(page).toHaveURL(/\/backoffice\/blog$/, { timeout: 8000 });
    await expect(page.getByText(/post excluído/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(TITLE)).toHaveCount(0);
  });

  test("página pública do post excluído mostra 'não encontrada', sem conteúdo antigo", async ({ page }) => {
    // fetchBlogPost usa cache: "no-store" (lib/blog.ts) especificamente pra
    // esse cenário: sem cache, não tem conteúdo velho pra ficar preso depois
    // de excluir/despublicar. O único resíduo conhecido é que o Next não
    // consegue reescrever o status HTTP pra 404 quando o notFound() acontece
    // em uma resposta já em streaming (limitação documentada do App Router,
    // não específica desse app) — por isso a asserção é sobre o conteúdo
    // renderizado, que é o que o usuário de fato vê, e não sobre `res.status()`.
    await page.goto(`/blog/${SLUG}`);
    await expect(page.getByText(/página não encontrada/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(TITLE)).toHaveCount(0);
  });
});
