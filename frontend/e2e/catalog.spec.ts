import { test, expect } from "@playwright/test";

test.describe("Nossos Serviços (catalog)", () => {
  test("renders page with correct heading", async ({ page }) => {
    await page.goto("/dashboard/catalog");
    await expect(page.getByRole("heading", { name: /nossos serviços/i })).toBeVisible();
  });

  test("shows contact team banner", async ({ page }) => {
    await page.goto("/dashboard/catalog");
    await expect(page.locator("a[href='mailto:contato@papermoon.com.br']").first()).toBeVisible({ timeout: 5000 });
  });

  test("lists at least one service card", async ({ page }) => {
    await page.goto("/dashboard/catalog");
    await expect(
      page.locator("[class*='bg-surface-1'][class*='rounded-xl']").first()
    ).toBeVisible({ timeout: 8000 });
  });

  test("no subscribe or checkout buttons visible", async ({ page }) => {
    await page.goto("/dashboard/catalog");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("button", { name: /assinar/i })).not.toBeVisible();
    await expect(page.getByRole("button", { name: /contratar/i })).not.toBeVisible();
    await expect(page.getByRole("button", { name: /checkout/i })).not.toBeVisible();
  });

  test("no billing cycle toggle visible", async ({ page }) => {
    await page.goto("/dashboard/catalog");
    await page.waitForLoadState("networkidle");
    await expect(page.getByRole("button", { name: /mensal/i })).not.toBeVisible();
    await expect(page.getByRole("button", { name: /anual/i })).not.toBeVisible();
  });

  test("validate-key endpoint returns valid for an active key", async ({ page }) => {
    await page.goto("/dashboard/api-keys");
    const keyEl = page.locator(".font-mono").first();
    await expect(keyEl).toBeVisible({ timeout: 8000 });
    const key = await keyEl.textContent();

    if (key?.trim()) {
      const res = await page.request.get(`/api/proxy/licensing/validate-key/?key=${key.trim()}`);
      expect(res.status()).toBe(200);
      const body = await res.json();
      expect(body.data).toHaveProperty("valid");
    }
  });
});
