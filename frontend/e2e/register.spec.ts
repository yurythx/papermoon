import { test, expect } from "@playwright/test";

/**
 * Self-registration flow.
 * Uses a unique e-mail per run so tests can run against a live DB without conflicts.
 * Requires: frontend (localhost:3000) + backend (localhost:8000) running.
 */

test.describe("Self-registration", () => {
  async function fillRegisterForm(
    page: import("@playwright/test").Page,
    data: { firstName?: string; lastName?: string; company?: string; email?: string; password?: string; confirm?: string }
  ) {
    if (data.firstName !== undefined) await page.getByLabel("Nome", { exact: true }).fill(data.firstName);
    if (data.lastName !== undefined) await page.getByLabel("Sobrenome", { exact: true }).fill(data.lastName);
    if (data.company !== undefined) await page.getByLabel("Nome da empresa", { exact: true }).fill(data.company);
    if (data.email !== undefined) await page.getByLabel("E-mail profissional").fill(data.email);
    const pwdInputs = page.locator('input[type="password"]');
    if (data.password !== undefined) await pwdInputs.nth(0).fill(data.password);
    if (data.confirm !== undefined) await pwdInputs.nth(1).fill(data.confirm);
  }

  test("register page renders correctly", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByRole("heading", { name: "Criar conta" })).toBeVisible();
    await expect(page.getByLabel("Nome", { exact: true })).toBeVisible();
    await expect(page.getByLabel("E-mail profissional")).toBeVisible();
    await expect(page.locator('input[type="password"]').first()).toBeVisible();
  });

  test("login page has link to register", async ({ page }) => {
    await page.goto("/login");
    const link = page.getByRole("link", { name: /criar conta/i });
    await expect(link).toBeVisible();
    await link.click();
    await expect(page).toHaveURL(/\/register/);
  });

  test("register with valid data redirects to onboarding", async ({ page }) => {
    const unique = Date.now();
    await page.goto("/register");

    await fillRegisterForm(page, {
      firstName: "Test",
      lastName: "User",
      company: "Test Corp E2E",
      email: `e2e_register_${unique}@test.com`,
      password: "secure1234",
      confirm: "secure1234",
    });

    await page.getByRole("button", { name: /criar conta/i }).click();
    await expect(page).toHaveURL(/\/onboarding/, { timeout: 10_000 });
  });

  test("register with mismatched passwords shows client error", async ({ page }) => {
    await page.goto("/register");

    await fillRegisterForm(page, {
      firstName: "Test",
      lastName: "User",
      company: "Corp",
      email: "mismatch@test.com",
      password: "secure1234",
      confirm: "different5678",
    });

    await page.getByRole("button", { name: /criar conta/i }).click();

    await expect(page).toHaveURL(/\/register/);
    await expect(page.locator("p.text-danger")).toBeVisible();
  });

  test("register with duplicate email shows server error", async ({ page }) => {
    await page.goto("/register");

    await fillRegisterForm(page, {
      firstName: "Dup",
      lastName: "Admin",
      company: "Dup Corp",
      email: "owner@acme.com",
      password: "secure1234",
      confirm: "secure1234",
    });

    await page.getByRole("button", { name: /criar conta/i }).click();

    await expect(page).toHaveURL(/\/register/);
    await expect(page.locator("p.text-danger")).toBeVisible();
  });
});
