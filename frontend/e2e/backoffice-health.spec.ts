import { test, expect } from "@playwright/test";

/**
 * Backoffice — system health page.
 * Requires: admin@papermoon.com / admin123 (from seed data).
 * The health endpoint (/health/) is a public GET — no auth required.
 * The page is at /backoffice/health and is admin-only in the UI.
 */

test.describe("Backoffice health", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/backoffice/health");
  });

  test("shows page heading", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /saúde|health|sistema|plataforma/i })
    ).toBeVisible({ timeout: 5000 });
  });

  test("shows DB service card", async ({ page }) => {
    await expect(page.getByText(/banco de dados|database|postgresql/i)).toBeVisible({ timeout: 5000 });
  });

  test("shows Redis service card", async ({ page }) => {
    await expect(page.getByText(/redis/i)).toBeVisible({ timeout: 5000 });
  });

  test("shows Celery service card", async ({ page }) => {
    await expect(page.getByText(/celery/i)).toBeVisible({ timeout: 5000 });
  });

  test("shows overall status banner", async ({ page }) => {
    // Banner shows one of these states; wait up to 8s for the API to resolve
    await expect(
      page.getByText(/operacionais|operacional|degradado|falha|verificando/i).first()
    ).toBeVisible({ timeout: 8000 });
  });

  test("service cards show a status label", async ({ page }) => {
    // Each card should have a status label (Operacional or a failure text)
    await expect(
      page.getByText(/operacional|ok|erro|falha/i).first()
    ).toBeVisible({ timeout: 5000 });
  });
});
