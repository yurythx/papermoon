import { test as setup, expect } from "@playwright/test";
import path from "path";

const adminAuthFile = path.join(__dirname, "../.auth/admin.json");

setup("authenticate as admin@papermoon.com", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel(/e-mail/i).fill("admin@papermoon.com");
  await page.locator("#password").fill("admin123");
  await page.getByRole("button", { name: /entrar/i }).click();
  await expect(page).toHaveURL(/\/dashboard|\/backoffice/, { timeout: 10_000 });
  await page.context().storageState({ path: adminAuthFile });
});
