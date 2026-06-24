import { test as setup, expect } from "@playwright/test";
import path from "path";

const authFile = path.join(__dirname, "../.auth/owner.json");

setup("authenticate as owner@acme.com", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel(/e-mail/i).fill("owner@acme.com");
  await page.locator("#password").fill("demo1234");
  await page.getByRole("button", { name: /entrar/i }).click();
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 10_000 });
  await page.context().storageState({ path: authFile });
});
