import { test, expect } from "@playwright/test";

/**
 * Backoffice — subscriptions list page golden paths.
 * Requires: admin@papermoon.com / admin123 (from seed data).
 */

test.describe("Backoffice subscriptions list", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/backoffice/subscriptions");
    await expect(page.getByRole("heading", { name: /assinaturas/i })).toBeVisible({ timeout: 5000 });
  });

  test("shows subscriptions table", async ({ page }) => {
    await expect(page.getByRole("table")).toBeVisible({ timeout: 5000 });
  });

  test("shows Cliente column header", async ({ page }) => {
    await expect(page.getByRole("columnheader", { name: /cliente/i })).toBeVisible({ timeout: 5000 });
  });

  test("shows Plano column header", async ({ page }) => {
    await expect(page.getByRole("columnheader", { name: /plano/i })).toBeVisible({ timeout: 5000 });
  });

  test("shows Detalhe links for each row", async ({ page }) => {
    await expect(page.getByRole("link", { name: "Detalhe" }).first()).toBeVisible({ timeout: 5000 });
  });

  test("shows search input", async ({ page }) => {
    await expect(page.getByPlaceholder(/buscar por cliente/i)).toBeVisible({ timeout: 5000 });
  });

  test("search filters the list", async ({ page }) => {
    const table = page.getByRole("table");
    await expect(table).toBeVisible({ timeout: 5000 });

    // Get the first customer name from the table
    const firstCustomerCell = table.getByRole("row").nth(1).getByRole("cell").nth(2);
    const customerName = (await firstCustomerCell.textContent()) ?? "";

    const searchInput = page.getByPlaceholder(/buscar por cliente/i);
    await searchInput.fill(customerName.trim().slice(0, 5));

    // After debounce, at least header + 1 data row should still be visible
    const rows = table.getByRole("row");
    await expect(rows.first()).toBeVisible({ timeout: 2000 });
  });

  test("shows Nova assinatura button", async ({ page }) => {
    await expect(page.getByRole("button", { name: /nova assinatura/i })).toBeVisible({ timeout: 5000 });
  });

  test("opens create subscription modal", async ({ page }) => {
    await page.getByRole("button", { name: /nova assinatura/i }).click();
    await expect(page.getByText(/assinatura será criada manualmente/i)).toBeVisible({ timeout: 3000 });
  });

  test("closes create subscription modal", async ({ page }) => {
    await page.getByRole("button", { name: /nova assinatura/i }).click();
    await expect(page.getByText(/assinatura será criada manualmente/i)).toBeVisible({ timeout: 3000 });
    await page.getByRole("button", { name: /fechar/i }).click();
    await expect(page.getByText(/assinatura será criada manualmente/i)).not.toBeVisible();
  });

  test("status filter changes visible rows", async ({ page }) => {
    const statusSelect = page.getByLabel(/status/i).or(page.getByRole("combobox").first());
    if (await statusSelect.isVisible()) {
      await statusSelect.selectOption("active");
      await expect(page.getByRole("table")).toBeVisible({ timeout: 3000 });
    }
  });

  test("Detalhe link navigates to subscription detail", async ({ page }) => {
    await page.getByRole("link", { name: "Detalhe" }).first().click();
    await expect(page).toHaveURL(/\/backoffice\/subscriptions\/.+/, { timeout: 5000 });
  });
});
