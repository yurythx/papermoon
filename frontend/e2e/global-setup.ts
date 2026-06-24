/**
 * Global setup — runs BEFORE all tests and Playwright projects.
 *
 * Ensures owner@acme.com has the expected seed password (demo1234).
 * If the forgot-password E2E test failed mid-way in a previous run, the
 * password may still be the temporary value. This routine detects and
 * restores it so the suite can start in a clean state.
 */

import { chromium, request as playwrightRequest } from "@playwright/test";

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";
const MAILHOG = "http://localhost:8025";
const SEED_EMAIL = "owner@acme.com";
const SEED_PASSWORD = "demo1234";
const TMP_PASSWORD = "NovaSenha@2025!";

async function globalSetup(): Promise<void> {
  // Clear MailHog inbox before the suite so the forgot-password test always
  // picks up its own email and MailHog stays fast (SMTP slows with many messages).
  // Delete per-message to avoid the hanging DELETE /api/v1/messages endpoint.
  const apiCtx = await playwrightRequest.newContext();
  try {
    const listRes = await apiCtx.get(`${MAILHOG}/api/v2/messages?limit=500`, { timeout: 5_000 });
    const listData = await listRes.json();
    const ids: string[] = (listData.items ?? []).map((m: { ID: string }) => m.ID);
    for (const id of ids) {
      await apiCtx.delete(`${MAILHOG}/api/v1/messages/${id}`, { timeout: 1_000 }).catch(() => {});
    }
    if (ids.length > 0) console.log(`[global-setup] Cleared ${ids.length} messages from MailHog`);
  } catch {
    // Best-effort — MailHog may be unavailable
  } finally {
    await apiCtx.dispose();
  }

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    // Try logging in with the seed password
    await page.goto(`${BASE_URL}/login`);
    await page.getByLabel(/e-mail/i).fill(SEED_EMAIL);
    await page.locator("#password").fill(SEED_PASSWORD);
    await page.getByRole("button", { name: /entrar/i }).click();
    await page.waitForURL(/\/dashboard/, { timeout: 8_000 }).catch(() => {});

    if (page.url().includes("/dashboard")) {
      // All good — seed password works
      return;
    }

    // Seed password failed — try TMP_PASSWORD (left by a failed forgot-password test)
    await page.goto(`${BASE_URL}/login`);
    await page.getByLabel(/e-mail/i).fill(SEED_EMAIL);
    await page.locator("#password").fill(TMP_PASSWORD);
    await page.getByRole("button", { name: /entrar/i }).click();
    await page.waitForURL(/\/dashboard/, { timeout: 8_000 }).catch(() => {});

    if (page.url().includes("/dashboard")) {
      // Restore seed password via change-password endpoint (uses browser cookies)
      const res = await page.request.post(`${BASE_URL}/api/proxy/auth/change-password/`, {
        data: { current_password: TMP_PASSWORD, new_password: SEED_PASSWORD },
        failOnStatusCode: false,
      });
      if (res.ok()) {
        console.log("[global-setup] Restored owner@acme.com password to demo1234");
      } else {
        console.warn("[global-setup] Failed to restore password:", await res.text());
      }
    } else {
      console.warn("[global-setup] Could not log in with either demo1234 or TMP_PASSWORD");
    }
  } finally {
    await browser.close();
  }
}

export default globalSetup;
