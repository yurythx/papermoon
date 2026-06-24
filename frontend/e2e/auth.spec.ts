import { test, expect } from "@playwright/test";

/**
 * Auth golden paths.
 * Requires: frontend (localhost:3000) + backend (localhost:8000) running with seed data.
 * Seed credentials: owner@acme.com / demo1234
 */

test.describe("Authentication", () => {
  test("login with valid credentials redirects to dashboard", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/e-mail/i).fill("owner@acme.com");
    await page.locator('#password').fill("demo1234");
    await page.getByRole("button", { name: /entrar/i }).click();
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("login with wrong password shows error", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/e-mail/i).fill("owner@acme.com");
    await page.locator('#password').fill("wrongpassword");
    await page.getByRole("button", { name: /entrar/i }).click();
    await expect(page.locator("p.text-danger")).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });

  test("unauthenticated user is redirected to login", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });

  test("logout clears session and redirects to login", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/e-mail/i).fill("owner@acme.com");
    await page.locator('#password').fill("demo1234");
    await page.getByRole("button", { name: /entrar/i }).click();
    await expect(page).toHaveURL(/\/dashboard/);

    // Open user menu dropdown, then click Sair
    await page.locator('button:has([class*="bg-brand-accent"])').click();
    await page.getByRole("button", { name: /sair/i }).click();
    await expect(page).toHaveURL(/\/login/);

    // Confirm the session is cleared — navigating to dashboard redirects back
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });
});
