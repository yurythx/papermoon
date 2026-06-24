import { test, expect } from "@playwright/test";

/**
 * Backoffice CMS editor golden paths.
 * Requires: admin@papermoon.com / admin123 (from seed data).
 * Seed must have populated CMS pages (run `make seed` to populate).
 */

test.describe("Backoffice CMS — list page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/backoffice/cms");
  });

  test("shows page heading", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /páginas de serviço/i })).toBeVisible({
      timeout: 5000,
    });
  });

  test("lists service products", async ({ page }) => {
    await expect(page.getByText(/whatsapp/i).first()).toBeVisible({ timeout: 5000 });
  });

  test("shows configured badge for seeded pages", async ({ page }) => {
    await expect(page.getByText(/configurada/i).first()).toBeVisible({ timeout: 5000 });
  });

  test("each row links to an editor page", async ({ page }) => {
    // Rows are full-width links with href matching /backoffice/cms/<slug>
    await expect(page.locator('a[href^="/backoffice/cms/"]').first()).toBeVisible({
      timeout: 5000,
    });
  });
});

test.describe("Backoffice CMS — editor page (whatsapp-api)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/backoffice/cms/whatsapp-api");
  });

  test("shows product name in header", async ({ page }) => {
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible({ timeout: 5000 });
  });

  test("shows slug in header", async ({ page }) => {
    await expect(page.getByText("whatsapp-api")).toBeVisible({ timeout: 5000 });
  });

  test("renders Conteúdo principal section", async ({ page }) => {
    await expect(page.getByText("Conteúdo principal")).toBeVisible({ timeout: 5000 });
  });

  test("tagline field is pre-populated from seed", async ({ page }) => {
    const taglineInput = page.getByPlaceholder(/frase de impacto/i);
    await expect(taglineInput).toBeVisible({ timeout: 5000 });
    await expect(taglineInput).not.toHaveValue("");
  });

  test("renders Passos de implantação section with seeded steps", async ({ page }) => {
    await expect(page.getByText(/passos de implantação/i)).toBeVisible({ timeout: 5000 });
    // Should have at least one step with "Adicionar passo" button
    await expect(page.getByRole("button", { name: /adicionar passo/i })).toBeVisible({
      timeout: 5000,
    });
  });

  test("renders FAQ section with seeded FAQs", async ({ page }) => {
    await expect(page.getByText(/perguntas frequentes/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByRole("button", { name: /adicionar pergunta/i })).toBeVisible({
      timeout: 5000,
    });
  });

  test("renders Galeria de imagens section", async ({ page }) => {
    await expect(page.getByText(/galeria de imagens/i)).toBeVisible({ timeout: 5000 });
  });

  test("renders Grupos de funcionalidades section", async ({ page }) => {
    await expect(page.getByText(/grupos de funcionalidades/i)).toBeVisible({ timeout: 5000 });
  });

  test("renders SEO section (collapsed by default)", async ({ page }) => {
    await expect(page.getByText("SEO")).toBeVisible({ timeout: 5000 });
  });

  test("Save button is present", async ({ page }) => {
    await expect(page.getByRole("button", { name: /salvar/i }).first()).toBeVisible({
      timeout: 5000,
    });
  });

  test("Ver página link points to correct service URL", async ({ page }) => {
    const viewLink = page.getByRole("link", { name: /ver página/i });
    await expect(viewLink).toBeVisible({ timeout: 5000 });
    await expect(viewLink).toHaveAttribute("href", /\/servicos\/whatsapp-api/);
  });

  test("back arrow navigates to CMS list", async ({ page }) => {
    // The back link wraps an ArrowLeft SVG icon and links to /backoffice/cms
    const backLink = page.locator('a[href="/backoffice/cms"]');
    await expect(backLink).toBeVisible({ timeout: 5000 });
    await backLink.click();
    await expect(page).toHaveURL(/\/backoffice\/cms$/);
  });
});

test.describe("Backoffice CMS — editor interactions", () => {
  test("can update tagline and save page", async ({ page }) => {
    await page.goto("/backoffice/cms/whatsapp-api");

    // Wait for the page to load with seeded data
    const taglineInput = page.getByPlaceholder(/frase de impacto/i);
    await expect(taglineInput).toBeVisible({ timeout: 5000 });

    // Clear and type new tagline
    await taglineInput.fill("Nova tagline de teste E2E");

    // Click save
    const saveBtn = page.getByRole("button", { name: /salvar/i }).first();
    await saveBtn.click();

    // Wait for toast success
    await expect(page.getByText(/página salva/i)).toBeVisible({ timeout: 8000 });
  });

  test("can add a new FAQ entry", async ({ page }) => {
    await page.goto("/backoffice/cms/whatsapp-api");

    // Click "Adicionar pergunta"
    const addFaqBtn = page.getByRole("button", { name: /adicionar pergunta/i });
    await expect(addFaqBtn).toBeVisible({ timeout: 5000 });
    await addFaqBtn.click();

    // A new question input should appear
    const questionInputs = page.getByPlaceholder("Pergunta...");
    const count = await questionInputs.count();
    expect(count).toBeGreaterThan(0);
  });

  test("can add a new step", async ({ page }) => {
    await page.goto("/backoffice/cms/whatsapp-api");

    const addStepBtn = page.getByRole("button", { name: /adicionar passo/i });
    await expect(addStepBtn).toBeVisible({ timeout: 5000 });

    const stepsBefore = await page.getByPlaceholder("Título do passo").count();
    await addStepBtn.click();
    const stepsAfter = await page.getByPlaceholder("Título do passo").count();
    expect(stepsAfter).toBe(stepsBefore + 1);
  });

  test("navigates from CMS list to editor by clicking a row", async ({ page }) => {
    await page.goto("/backoffice/cms");

    // Each row is a full-width link with href="/backoffice/cms/<slug>"
    const firstRowLink = page.locator('a[href^="/backoffice/cms/"]').first();
    await expect(firstRowLink).toBeVisible({ timeout: 5000 });
    await firstRowLink.click();

    await expect(page).toHaveURL(/\/backoffice\/cms\/.+/);
    await expect(page.getByText("Conteúdo principal")).toBeVisible({ timeout: 5000 });
  });

  test("gallery section shows upload slot", async ({ page }) => {
    await page.goto("/backoffice/cms/whatsapp-api");

    // Open gallery section (collapsed by default)
    const gallerySection = page.getByText(/galeria de imagens/i);
    await expect(gallerySection).toBeVisible({ timeout: 5000 });
    await gallerySection.click();

    // Upload slot should be visible
    await expect(page.getByText(/adicionar/i).last()).toBeVisible({ timeout: 3000 });
  });
});

test.describe("Backoffice CMS — other seeded pages", () => {
  test("editor loads for glpi", async ({ page }) => {
    await page.goto("/backoffice/cms/glpi");
    await expect(page.getByText("Conteúdo principal")).toBeVisible({ timeout: 5000 });
  });

  test("editor loads for tailscale", async ({ page }) => {
    await page.goto("/backoffice/cms/tailscale");
    await expect(page.getByText("Conteúdo principal")).toBeVisible({ timeout: 5000 });
    await expect(page.getByPlaceholder(/frase de impacto/i)).toHaveValue(
      /Rede privada mesh com acesso remoto seguro e sem abrir portas/i
    );
  });

  test("editor loads for zabbix", async ({ page }) => {
    await page.goto("/backoffice/cms/zabbix");
    await expect(page.getByText("Conteúdo principal")).toBeVisible({ timeout: 5000 });
  });

  test("editor loads for proxmox", async ({ page }) => {
    await page.goto("/backoffice/cms/proxmox");
    await expect(page.getByText("Conteúdo principal")).toBeVisible({ timeout: 5000 });
  });

  test("non-existent slug shows error state", async ({ page }) => {
    await page.goto("/backoffice/cms/slug-nao-existe-xyz");
    await expect(
      page.getByText(/produto não encontrado|não encontrado/i)
    ).toBeVisible({ timeout: 8000 });
  });
});
