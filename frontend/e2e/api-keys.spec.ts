import { test, expect } from "@playwright/test";

test.describe("API Keys", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
  });

  test("navigate to API Keys page", async ({ page }) => {
    await page.getByRole("link", { name: "API Keys" }).click();
    await expect(page).toHaveURL(/\/dashboard\/api-keys/);
    await expect(page.getByRole("heading", { name: /api keys/i })).toBeVisible();
  });

  test("quota card shows usage stats", async ({ page }) => {
    await page.goto("/dashboard/api-keys");
    // Quota card renders with call count text
    await expect(page.getByText(/chamadas/i).first()).toBeVisible({ timeout: 8000 });
    // Progress bar is present
    await expect(page.locator(".h-1\\.5.bg-surface-3").first()).toBeVisible();
  });

  test("daily usage chart renders with seed data", async ({ page }) => {
    await page.goto("/dashboard/api-keys");
    // Chart heading visible (seed data provides non-zero usage for acme)
    await expect(page.getByText(/uso diário/i)).toBeVisible({ timeout: 8000 });
    // Total calls summary in the chart header
    await expect(page.getByText(/chamadas em 30 dias/i)).toBeVisible();
  });

  test("generate new API key and see it listed", async ({ page }) => {
    await page.goto("/dashboard/api-keys");
    // Count "Revogar" buttons before — one per active key
    const before = await page.getByRole("button", { name: /revogar/i }).count();

    await page.getByRole("button", { name: /gerar.*chave|nova.*api key/i }).click();

    // New key appears highlighted with success-muted background (may be multiple if seeds exist)
    await expect(page.locator("[class*='bg-success-muted']").first()).toBeVisible({ timeout: 5000 });
    const after = await page.getByRole("button", { name: /revogar/i }).count();
    expect(after).toBeGreaterThan(before);
  });

  test("revoke an API key", async ({ page }) => {
    await page.goto("/dashboard/api-keys");

    // Wait for keys to load
    await expect(page.getByRole("button", { name: /revogar/i }).first()).toBeVisible({ timeout: 5000 });

    const beforeCount = await page.getByRole("button", { name: /revogar/i }).count();
    await page.getByRole("button", { name: /revogar/i }).first().click();

    // After revoke, one "Revogar" button disappears (key moves to Revogadas section)
    await expect(page.getByRole("button", { name: /revogar/i })).toHaveCount(
      beforeCount - 1,
      { timeout: 10000 }
    );
  });
});
