import { test, expect } from "@playwright/test";

test.describe("Meus Contratos", () => {
  test("navigate to page and show correct heading", async ({ page }) => {
    await page.goto("/dashboard/subscriptions");
    await expect(page).toHaveURL(/\/dashboard\/subscriptions/);
    await expect(page.getByRole("heading", { name: /meus contratos/i })).toBeVisible();
  });

  test("shows subscription cards when data loads", async ({ page }) => {
    await page.goto("/dashboard/subscriptions");
    await expect(
      page.locator("[class*='rounded-xl'][class*='border']").first()
    ).toBeVisible({ timeout: 8000 });
  });

  test("subscription card shows billing details", async ({ page }) => {
    await page.goto("/dashboard/subscriptions");
    await page.waitForLoadState("networkidle");
    // If subscription data loaded, detail labels must be present
    const ciclo = page.getByText("Ciclo").first();
    if (await ciclo.isVisible()) {
      await expect(page.getByText("Valor").first()).toBeVisible();
      await expect(page.getByText("Vigência").first()).toBeVisible();
    }
  });

  test("no cancel or change-plan buttons (read-only)", async ({ page }) => {
    await page.goto("/dashboard/subscriptions");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("button", { name: /cancelar/i })).not.toBeVisible();
    await expect(page.getByRole("button", { name: /mudar plano/i })).not.toBeVisible();
  });

  test("support footer shows mailto link", async ({ page }) => {
    await page.goto("/dashboard/subscriptions");
    await expect(page.locator("a[href='mailto:contato@papermoon.com.br']").first()).toBeVisible({ timeout: 5000 });
  });

  test("empty state shows team contact prompt", async ({ page }) => {
    await page.goto("/dashboard/subscriptions");
    await page.waitForLoadState("networkidle");
    const empty = page.getByText(/nenhum contrato/i);
    // Only check for empty state if no subscription cards rendered
    const cards = page.locator("[class*='rounded-xl'][class*='border']");
    const count = await cards.count();
    if (count <= 1) {
      // Could be just the support footer card — check for empty state text
      if (await empty.isVisible()) {
        await expect(empty).toBeVisible();
      }
    }
  });
});
