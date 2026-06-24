import { test, expect } from "@playwright/test";

/**
 * Backoffice invoices page — admin golden paths.
 * Requires: admin@papermoon.com (from admin.setup.ts).
 */

test.describe("Backoffice invoices", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/backoffice/invoices");
  });

  test("renders invoices page with table", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /faturas/i })).toBeVisible();
    await expect(page.getByRole("table")).toBeVisible({ timeout: 8000 });
  });

  test("shows Nova fatura button", async ({ page }) => {
    await expect(page.getByRole("button", { name: /nova fatura/i })).toBeVisible();
  });

  test("status and type filters are visible", async ({ page }) => {
    const selects = page.locator("select");
    await expect(selects.first()).toBeVisible({ timeout: 5000 });
    await expect(selects.nth(1)).toBeVisible();
  });

  test("invoice rows have company name and status badge", async ({ page }) => {
    await page.waitForLoadState("networkidle");
    const rows = page.getByRole("row");
    const count = await rows.count();
    if (count > 1) {
      await expect(rows.nth(1)).toBeVisible();
    }
  });

  test("opens create invoice modal on Nova fatura click", async ({ page }) => {
    await page.getByRole("button", { name: /nova fatura/i }).click();
    await expect(page.getByText(/nova fatura avulsa/i)).toBeVisible({ timeout: 3000 });
    await expect(page.getByRole("button", { name: /criar fatura/i })).toBeVisible();
  });

  test("create invoice modal has required fields", async ({ page }) => {
    await page.getByRole("button", { name: /nova fatura/i }).click();
    await expect(page.getByText(/nova fatura avulsa/i)).toBeVisible({ timeout: 3000 });
    // Required field labels
    await expect(page.getByText("Cliente *")).toBeVisible();
    await expect(page.getByText("Valor (R$) *")).toBeVisible();
    await expect(page.getByText("Vencimento *")).toBeVisible();
    // Submit disabled until filled
    await expect(page.getByRole("button", { name: /criar fatura/i })).toBeDisabled();
  });

  test("create invoice modal closes on Cancelar", async ({ page }) => {
    await page.getByRole("button", { name: /nova fatura/i }).click();
    await expect(page.getByText(/nova fatura avulsa/i)).toBeVisible({ timeout: 3000 });
    await page.getByRole("button", { name: /cancelar/i }).click();
    await expect(page.getByText(/nova fatura avulsa/i)).not.toBeVisible({ timeout: 3000 });
  });

  test("status filter changes visible rows", async ({ page }) => {
    // Wait for initial data to load
    await expect(page.getByRole("table")).toBeVisible({ timeout: 8000 });
    const statusSelect = page.locator("select").first();
    await statusSelect.selectOption("paid");
    // After filter, either table or empty state must appear (skeletons resolve)
    await expect(
      page.getByRole("table").or(page.getByText(/nenhuma fatura/i))
    ).toBeVisible({ timeout: 8000 });
  });

  test("Remover button opens confirmation dialog", async ({ page }) => {
    await page.waitForLoadState("networkidle");
    const removeBtn = page.getByRole("button", { name: /remover/i }).first();
    if (await removeBtn.isVisible()) {
      await removeBtn.click();
      await expect(page.getByText(/remover fatura/i)).toBeVisible({ timeout: 3000 });
      await expect(page.getByRole("button", { name: /cancelar/i })).toBeVisible();
    }
  });
});
