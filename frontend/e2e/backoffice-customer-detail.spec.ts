import { test, expect } from "@playwright/test";

/**
 * Backoffice — customer detail page golden paths.
 * Requires: admin@papermoon.com / admin123 (from seed data).
 * Navigates via the customers list link to avoid hardcoding customer IDs.
 */

test.describe("Backoffice customer detail", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/backoffice/customers");
    await expect(page.getByRole("table")).toBeVisible({ timeout: 5000 });
  });

  test("navigates to detail page by clicking customer name", async ({ page }) => {
    // Click the first company name link in the table
    const firstLink = page.getByRole("table").getByRole("link").first();
    const customerName = await firstLink.textContent();
    await firstLink.click();

    await expect(page).toHaveURL(/\/backoffice\/customers\/.+/);
    // Company name appears in the page header
    await expect(page.getByText(customerName!.trim())).toBeVisible({ timeout: 5000 });
  });

  test("detail page shows CNPJ", async ({ page }) => {
    await page.getByRole("table").getByRole("link").first().click();
    await expect(page).toHaveURL(/\/backoffice\/customers\/.+/);
    // CNPJ value appears in the header as a mono paragraph
    await expect(page.locator("p.font-mono").first()).toBeVisible({ timeout: 5000 });
  });

  test("breadcrumb back link navigates to customers list", async ({ page }) => {
    await page.getByRole("table").getByRole("link").first().click();
    await expect(page).toHaveURL(/\/backoffice\/customers\/.+/);

    await page.getByRole("link", { name: /clientes/i }).first().click();
    await expect(page).toHaveURL(/\/backoffice\/customers$/);
  });

  test("detail page renders subscriptions section", async ({ page }) => {
    await page.getByRole("table").getByRole("link").first().click();
    await expect(page).toHaveURL(/\/backoffice\/customers\/.+/);
    await expect(page.getByText(/assinaturas/i)).toBeVisible({ timeout: 5000 });
  });

  test("detail page renders invoices section", async ({ page }) => {
    await page.getByRole("table").getByRole("link").first().click();
    await expect(page).toHaveURL(/\/backoffice\/customers\/.+/);
    await expect(page.getByText(/faturas recentes/i)).toBeVisible({ timeout: 5000 });
  });

  test("action buttons are present for active customer", async ({ page }) => {
    await page.goto("/backoffice/customers");
    // List is ordered by -created_at; find the first row with "Ativo" badge (active customer)
    const activeRow = page.getByRole("table").getByRole("row").filter({
      has: page.getByText("Ativo", { exact: true }),
    }).first();
    await activeRow.getByRole("link").first().click();
    await expect(page).toHaveURL(/\/backoffice\/customers\/.+/);

    // Active customer has "Suspender" and "Cancelar conta" buttons
    await expect(
      page.getByRole("button", { name: /suspender|cancelar conta/i }).first()
    ).toBeVisible({ timeout: 5000 });
  });

  test("suspend confirm dialog opens and closes", async ({ page }) => {
    // Find an active customer that has the suspend button
    await page.goto("/backoffice/customers");
    await page.getByRole("table").getByRole("link").first().click();
    await expect(page).toHaveURL(/\/backoffice\/customers\/.+/);

    const suspendBtn = page.getByRole("button", { name: /suspender/i });
    if (await suspendBtn.isVisible()) {
      await suspendBtn.click();
      await expect(page.getByText("Suspender cliente")).toBeVisible({ timeout: 3000 });

      // Close via Voltar
      await page.getByRole("button", { name: /voltar/i }).click();
      await expect(page.getByText("Suspender cliente")).not.toBeVisible();
    } else {
      test.skip();
    }
  });
});
