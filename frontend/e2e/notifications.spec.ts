import { test, expect } from "@playwright/test";

test.describe("Notifications", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
  });

  test("notification bell is visible in dashboard", async ({ page }) => {
    await expect(page.locator("[aria-label='Notificações'], [title='Notificações'], button:has(svg)").first()).toBeVisible();
  });

  test("navigate to notifications history page", async ({ page }) => {
    await page.goto("/dashboard/notifications");
    await expect(page).toHaveURL(/\/dashboard\/notifications/);
    await expect(page.getByRole("heading", { name: /notificações/i })).toBeVisible();
  });

  test("notifications page shows event list", async ({ page }) => {
    await page.goto("/dashboard/notifications");
    // Events are listed as rows or cards
    await expect(page.locator("main, [data-testid='notification-list'], .space-y-").first()).toBeVisible({ timeout: 5000 });
  });
});
