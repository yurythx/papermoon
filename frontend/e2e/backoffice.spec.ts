import { test, expect } from "@playwright/test";

/**
 * Backoffice golden paths.
 * Requires: admin@papermoon.com / admin123 (from seed data).
 */

test.describe("Backoffice", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/backoffice");
  });

  test.describe("Metrics dashboard — KPI cards", () => {
    test("shows MRR card", async ({ page }) => {
      await expect(page.getByText("MRR")).toBeVisible({ timeout: 5000 });
    });

    test("shows ARR card", async ({ page }) => {
      await expect(page.getByText("ARR")).toBeVisible({ timeout: 5000 });
    });

    test("shows active customers card", async ({ page }) => {
      await expect(page.getByText("Clientes ativos")).toBeVisible({ timeout: 5000 });
    });

    test("shows churn this month card", async ({ page }) => {
      await expect(page.getByText("Churn este mês")).toBeVisible({ timeout: 5000 });
    });

    test("shows churn rate card", async ({ page }) => {
      await expect(page.getByText("Taxa de churn")).toBeVisible({ timeout: 5000 });
    });

    test("shows at-risk card", async ({ page }) => {
      await expect(page.getByText("Em risco")).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe("Metrics dashboard — charts", () => {
    test("shows monthly revenue section", async ({ page }) => {
      await expect(page.getByText(/receita mensal/i)).toBeVisible({ timeout: 5000 });
    });

    test("shows revenue by plan section", async ({ page }) => {
      await expect(page.getByText("Receita por plano")).toBeVisible({ timeout: 5000 });
    });

    test("shows API usage table", async ({ page }) => {
      await expect(page.getByText("Uso de API por cliente")).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe("Customers", () => {
    test("navigate to backoffice customers", async ({ page }) => {
      await page.goto("/backoffice/customers");
      await expect(page.getByRole("heading", { name: /clientes/i })).toBeVisible({ timeout: 5000 });
    });

    test("backoffice customers shows customer list", async ({ page }) => {
      await page.goto("/backoffice/customers");
      await expect(page.getByRole("table")).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe("Other sections", () => {
    test("navigate to backoffice invoices", async ({ page }) => {
      await page.goto("/backoffice/invoices");
      await expect(page.getByRole("heading", { name: /faturas/i })).toBeVisible({ timeout: 5000 });
    });

    test("navigate to backoffice subscriptions", async ({ page }) => {
      await page.goto("/backoffice/subscriptions");
      await expect(page.getByRole("heading", { name: /assinaturas/i })).toBeVisible({ timeout: 5000 });
    });

    test("navigate to audit log", async ({ page }) => {
      await page.goto("/backoffice/audit");
      await expect(page.getByRole("heading", { name: /audit/i })).toBeVisible({ timeout: 5000 });
    });

    test("navigate to products page", async ({ page }) => {
      await page.goto("/backoffice/products");
      await expect(page.getByRole("heading", { name: /produtos/i })).toBeVisible({ timeout: 5000 });
    });
  });
});
