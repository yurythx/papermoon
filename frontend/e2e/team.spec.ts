import { test, expect } from "@playwright/test";

test.describe("Team management", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
  });

  test("team page lists current members", async ({ page }) => {
    await page.goto("/dashboard/team");
    await expect(page.getByRole("heading", { name: /equipe/i })).toBeVisible();
    await expect(page.getByText("owner@acme.com")).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("(você)")).toBeVisible();
  });

  test("owner sees invite form", async ({ page }) => {
    await page.goto("/dashboard/team");
    await expect(page.getByPlaceholder(/email@empresa.com/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByRole("button", { name: /convidar/i })).toBeVisible();
  });

  test("send invitation creates pending entry", async ({ page }) => {
    // Use TechFlow (Pro plan, max_users=10) — Acme is at its Starter limit (max_users=3).
    // Clear the Acme storageState cookies so the /login page is accessible.
    await page.context().clearCookies();
    await page.goto("/login");
    await page.getByLabel(/e-mail/i).fill("owner@techflow.com");
    await page.locator('#password').fill("demo1234");
    await page.getByRole("button", { name: /entrar/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10_000 });

    // Revoke any leftover E2E invitations from previous runs to stay under max_users=10
    const listRes = await page.request.get("/api/proxy/client/invitations/", { failOnStatusCode: false });
    if (listRes.ok()) {
      const body = await listRes.json();
      const invitations: Array<{ id: string; email: string; status: string }> =
        body?.data ?? body ?? [];
      for (const inv of invitations) {
        if (inv.status === "pending" && inv.email.startsWith("e2e-")) {
          await page.request.delete(`/api/proxy/client/invitations/${inv.id}/`, {
            failOnStatusCode: false,
          });
        }
      }
    }

    await page.goto("/dashboard/team");
    await expect(page.getByPlaceholder(/email@empresa.com/i)).toBeVisible({ timeout: 5000 });

    const uniqueEmail = `e2e-${Date.now()}@test.com`;
    await page.getByPlaceholder(/email@empresa.com/i).fill(uniqueEmail);
    await page.getByRole("button", { name: /convidar/i }).click();

    await expect(page.getByText(/convite enviado/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(uniqueEmail)).toBeVisible({ timeout: 5000 });
  });
});
