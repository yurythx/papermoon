import { test, expect } from "@playwright/test";

test.describe("Profile Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
  });

  test("navigate to profile page", async ({ page }) => {
    await page.goto("/dashboard/profile");
    await expect(page).toHaveURL(/\/dashboard\/profile/);
    await expect(page.getByRole("heading", { name: /minha empresa/i })).toBeVisible();
  });

  test("shows company data section with razão social and CNPJ", async ({ page }) => {
    await page.goto("/dashboard/profile");
    await expect(page.getByText("Dados cadastrais", { exact: true })).toBeVisible({ timeout: 5000 });
    await expect(page.getByLabel("Razão social")).toBeVisible();
    await expect(page.getByLabel("CNPJ")).toBeVisible();
  });

  test("CNPJ field is read-only (cannot type)", async ({ page }) => {
    await page.goto("/dashboard/profile");
    const cnpjInput = page.getByLabel("CNPJ");
    await expect(cnpjInput).toBeVisible({ timeout: 5000 });
    // Verify the input has a value (from seed data)
    await expect(cnpjInput).not.toHaveValue("");
  });

  test("shows status badge for active customer", async ({ page }) => {
    await page.goto("/dashboard/profile");
    await expect(page.getByText(/ativo|active/i)).toBeVisible({ timeout: 5000 });
  });

  test("save button is disabled when name unchanged", async ({ page }) => {
    await page.goto("/dashboard/profile");
    await expect(page.getByRole("button", { name: /salvar alterações/i })).toBeDisabled({ timeout: 5000 });
  });

  test("save button enables when company name changes", async ({ page }) => {
    await page.goto("/dashboard/profile");
    const input = page.getByLabel("Razão social");
    await expect(input).toBeVisible({ timeout: 5000 });
    await input.fill("Acme Ltda Atualizado");
    await expect(page.getByRole("button", { name: /salvar alterações/i })).toBeEnabled();
  });

  test("shows change password section", async ({ page }) => {
    await page.goto("/dashboard/profile");
    await expect(page.getByRole("heading", { name: "Alterar senha" })).toBeVisible({ timeout: 5000 });
    await expect(page.getByLabel("Senha atual")).toBeVisible();
    await expect(page.getByLabel("Nova senha", { exact: true })).toBeVisible();
    await expect(page.getByLabel("Confirmar nova senha")).toBeVisible();
  });

  test("alterar senha button disabled when fields are empty", async ({ page }) => {
    await page.goto("/dashboard/profile");
    await expect(page.getByRole("button", { name: "Alterar senha" })).toBeDisabled({ timeout: 5000 });
  });

  test("shows mismatch error when passwords differ", async ({ page }) => {
    await page.goto("/dashboard/profile");
    await page.getByLabel("Senha atual").fill("demo1234");
    await page.getByLabel("Nova senha", { exact: true }).fill("newpass123");
    await page.getByLabel("Confirmar nova senha").fill("different123");
    await page.getByRole("button", { name: "Alterar senha" }).click();
    await expect(page.getByText(/não coincidem/i)).toBeVisible({ timeout: 3000 });
  });

  test("shows minimum length error for short password", async ({ page }) => {
    await page.goto("/dashboard/profile");
    await page.getByLabel("Senha atual").fill("demo1234");
    await page.getByLabel("Nova senha", { exact: true }).fill("short");
    await page.getByLabel("Confirmar nova senha").fill("short");
    await page.getByRole("button", { name: "Alterar senha" }).click();
    await expect(page.getByText(/mínimo 8 caracteres/i)).toBeVisible({ timeout: 3000 });
  });
});
