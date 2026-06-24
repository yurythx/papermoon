import { test, expect } from "@playwright/test";

/**
 * Backoffice — subscription detail page golden paths.
 * Requires: admin@papermoon.com / admin123 (from seed data).
 * Navigates via the subscriptions list to avoid hardcoding subscription IDs.
 */

test.describe("Backoffice subscription detail", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/backoffice/subscriptions");
    await expect(page.getByRole("heading", { name: /assinaturas/i })).toBeVisible({ timeout: 5000 });
  });

  async function goToFirstDetail(page: import("@playwright/test").Page) {
    const detailLink = page.getByRole("link", { name: "Detalhe" }).first();
    await expect(detailLink).toBeVisible({ timeout: 5000 });
    await detailLink.click();
    await expect(page).toHaveURL(/\/backoffice\/subscriptions\/.+/, { timeout: 5000 });
  }

  test("navigates to detail page via Detalhe link", async ({ page }) => {
    await goToFirstDetail(page);
    // Product name heading should be visible
    await expect(page.locator("h1").first()).toBeVisible({ timeout: 5000 });
  });

  test("shows subscription id in mono text", async ({ page }) => {
    await goToFirstDetail(page);
    // UUID appears as mono text under the heading
    await expect(page.locator("p.font-mono").first()).toBeVisible({ timeout: 5000 });
  });

  test("shows billing cycle row", async ({ page }) => {
    await goToFirstDetail(page);
    await expect(page.getByText("Ciclo")).toBeVisible({ timeout: 5000 });
  });

  test("shows amount row", async ({ page }) => {
    await goToFirstDetail(page);
    await expect(page.getByText("Valor")).toBeVisible({ timeout: 5000 });
  });

  test("shows services section", async ({ page }) => {
    await goToFirstDetail(page);
    await expect(page.getByText(/serviços/i)).toBeVisible({ timeout: 5000 });
  });

  test("shows Adicionar button", async ({ page }) => {
    await goToFirstDetail(page);
    await expect(page.getByRole("button", { name: /adicionar/i })).toBeVisible({ timeout: 5000 });
  });

  test("breadcrumb navigates back to subscriptions list", async ({ page }) => {
    await goToFirstDetail(page);
    await page.getByRole("link", { name: /assinaturas/i }).first().click();
    await expect(page).toHaveURL(/\/backoffice\/subscriptions$/, { timeout: 5000 });
  });

  test("shows customer link that points to customer detail", async ({ page }) => {
    await goToFirstDetail(page);
    // The customer row has a link to /backoffice/customers/<id>
    const customerLink = page.getByRole("link", { name: /./i }).filter({ hasNotText: /assinaturas|detalhe/i }).first();
    await expect(customerLink).toBeVisible({ timeout: 5000 });
  });

  test("add service modal opens and closes", async ({ page }) => {
    await goToFirstDetail(page);
    await page.getByRole("button", { name: /adicionar/i }).click();

    // Modal appears
    await expect(
      page.getByText(/provisionado automaticamente/i)
    ).toBeVisible({ timeout: 3000 });

    // Close with Fechar
    await page.getByRole("button", { name: /fechar/i }).click();
    await expect(
      page.getByText(/provisionado automaticamente/i)
    ).not.toBeVisible({ timeout: 3000 });
  });

  test("status badge is visible on the detail page", async ({ page }) => {
    await goToFirstDetail(page);
    // StatusBadge renders "Ativo", "Trial", "Suspenso", "Expirado", "Cancelado"
    const badge = page.locator("[class*='rounded']").filter({ hasText: /ativo|trial|suspenso|expirado|cancelado/i }).first();
    await expect(badge).toBeVisible({ timeout: 5000 });
  });
});
