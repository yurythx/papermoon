import { type Page, test, expect } from "@playwright/test";

/**
 * Forgot-password and reset-password golden paths.
 * Requires: frontend (localhost:3000) + backend (localhost:8000) + MailHog (localhost:8025) running.
 * Seed credentials: owner@acme.com / demo1234
 */

const MAILHOG = "http://localhost:8025";
const SEED_EMAIL = "owner@acme.com";
const SEED_PASSWORD = "demo1234";
const TMP_PASSWORD = "NovaSenha@2025!";

type MimePart = { Headers: Record<string, string[]>; Body: string };

/** Decode a MIME part body according to its Content-Transfer-Encoding header. */
function decodeMimePart(part: MimePart): string {
  const cte = (part.Headers?.["Content-Transfer-Encoding"]?.[0] ?? "").toLowerCase().trim();
  if (cte === "base64") {
    return Buffer.from(part.Body.replace(/\s/g, ""), "base64").toString("utf-8");
  }
  if (cte === "quoted-printable") {
    return part.Body
      .replace(/=\r?\n/g, "")
      .replace(/=([0-9A-Fa-f]{2})/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)));
  }
  return part.Body; // 7bit / 8bit — no decoding needed
}

/** Decode common HTML entities so URLs extracted from HTML are navigable. */
function decodeHtmlEntities(s: string): string {
  return s
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

/**
 * Snapshot the current email count for SEED_EMAIL in MailHog.
 * Call this BEFORE triggering the action that sends the email.
 */
async function getEmailCount(page: Page): Promise<number> {
  try {
    const resp = await page.request.get(
      `${MAILHOG}/api/v2/search?kind=to&query=${encodeURIComponent(SEED_EMAIL)}&limit=1`
    );
    const data = await resp.json();
    return data.total ?? 0;
  } catch {
    return 0;
  }
}

/**
 * Poll MailHog until a NEW email addressed to SEED_EMAIL arrives (total > countBefore).
 * Using count comparison instead of timestamps avoids clock-skew between host and Docker.
 */
async function waitForEmail(page: Page, countBefore: number, maxMs = 30_000): Promise<string> {
  const deadline = Date.now() + maxMs;
  while (Date.now() < deadline) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let data: any;
    try {
      const resp = await page.request.get(
        `${MAILHOG}/api/v2/search?kind=to&query=${encodeURIComponent(SEED_EMAIL)}&limit=20`
      );
      data = await resp.json();
    } catch {
      // MailHog can ECONNRESET under load — back off and retry
      await page.waitForTimeout(1_000);
      continue;
    }
    if ((data.total ?? 0) > countBefore) {
      // Take the most recent message (items[0])
      const item = data.items[0];
      if (!item) {
        await page.waitForTimeout(500);
        continue;
      }
      const parts: Array<MimePart & { Parts?: MimePart[] }> = item.MIME?.Parts ?? [];

      // Walk top-level parts first
      for (const part of parts) {
        const ct = (part.Headers?.["Content-Type"]?.[0] ?? "").toLowerCase();
        if (ct.includes("text/html") && part.Body) return decodeMimePart(part);
      }
      // Then nested parts (some mailers wrap in an outer multipart)
      for (const part of parts) {
        for (const np of part.Parts ?? []) {
          const ct = (np.Headers?.["Content-Type"]?.[0] ?? "").toLowerCase();
          if (ct.includes("text/html") && np.Body) return decodeMimePart(np);
        }
      }
      // Last resort: raw Content.Body (already assembled by MailHog, no MIME decoding needed)
      const rawBody: string = item.Content?.Body ?? "";
      if (rawBody) return rawBody;
    }
    await page.waitForTimeout(500);
  }
  throw new Error("MailHog: no email arrived within timeout");
}

test.describe("ForgotPassword flow", () => {
  test("renders split-screen layout with branding panel on desktop", async ({ page }) => {
    await page.goto("/forgot-password");
    await expect(page.getByRole("heading", { name: /atenda no whatsapp/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /redefinir senha/i })).toBeVisible();
    await expect(page.getByPlaceholder(/voce@empresa\.com/i)).toBeVisible();
  });

  test("shows success state after submitting email", async ({ page }) => {
    await page.goto("/forgot-password");
    await page.getByPlaceholder(/voce@empresa\.com/i).fill(SEED_EMAIL);
    await page.getByRole("button", { name: /enviar link/i }).click();
    await expect(page.getByRole("heading", { name: /verifique seu e-mail/i })).toBeVisible();
  });

  test("has link back to login", async ({ page }) => {
    await page.goto("/forgot-password");
    await expect(page.getByRole("link", { name: /voltar/i })).toHaveAttribute("href", "/login");
  });
});

test.describe("ResetPassword page", () => {
  test("shows invalid link state when uid/token are missing", async ({ page }) => {
    await page.goto("/reset-password");
    await expect(page.getByText(/link inválido/i)).toBeVisible();
    await expect(page.getByRole("link", { name: /solicitar novo link/i })).toHaveAttribute(
      "href",
      "/forgot-password"
    );
  });

  test("renders new-password form when uid and token are present", async ({ page }) => {
    await page.goto("/reset-password?uid=abc123&token=tok456");
    await expect(page.getByPlaceholder(/mínimo 8 caracteres/i)).toBeVisible();
    await expect(page.getByPlaceholder(/repita a senha/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /redefinir senha/i })).toBeVisible();
  });

  test("shows mismatch error when passwords differ", async ({ page }) => {
    await page.goto("/reset-password?uid=abc123&token=tok456");
    await page.getByPlaceholder(/mínimo 8 caracteres/i).fill("Senha123!");
    await page.getByPlaceholder(/repita a senha/i).fill("Diferente!");
    await page.getByRole("button", { name: /redefinir senha/i }).click();
    await expect(page.getByText(/senhas não coincidem/i)).toBeVisible();
  });

  test("full reset flow: email link → new password → login", async ({ page }) => {
    test.setTimeout(60_000); // email delivery + all steps can exceed the default 30s

    // Snapshot email count BEFORE requesting reset (avoids clock-skew issues with Docker)
    const countBefore = await getEmailCount(page);

    // Step 1: request password reset
    await page.goto("/forgot-password");
    await page.getByPlaceholder(/voce@empresa\.com/i).fill(SEED_EMAIL);
    await page.getByRole("button", { name: /enviar link/i }).click();
    await expect(page.getByRole("heading", { name: /verifique seu e-mail/i })).toBeVisible();

    // Step 2: fetch email body from MailHog — poll until count increases beyond snapshot
    const body = await waitForEmail(page, countBefore);
    expect(body).toContain("reset-password");

    // Step 3: extract reset link — &amp; in href attr must be decoded back to &
    const match = body.match(/http:\/\/localhost:3000\/reset-password\?[^"<>\s\r\n]*/);
    expect(match, "Reset link not found in email body").not.toBeNull();
    const resetUrl = decodeHtmlEntities(match![0]);

    // Step 4: navigate to reset page and set new password
    await page.goto(resetUrl);
    await expect(page.getByPlaceholder(/mínimo 8 caracteres/i)).toBeVisible();
    await page.getByPlaceholder(/mínimo 8 caracteres/i).fill(TMP_PASSWORD);
    await page.getByPlaceholder(/repita a senha/i).fill(TMP_PASSWORD);
    await page.getByRole("button", { name: /redefinir senha/i }).click();

    // Step 5: confirm redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 8_000 });

    // Step 6: log in with new password to prove the reset worked
    await page.getByLabel(/e-mail/i).fill(SEED_EMAIL);
    await page.locator("#password").fill(TMP_PASSWORD);
    await page.getByRole("button", { name: /entrar/i }).click();
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 8_000 });

    // Step 7: restore seed password so other tests remain green
    // page.request sends the browser cookies (access token set during login above)
    const restoreRes = await page.request.post("/api/proxy/auth/change-password/", {
      data: { current_password: TMP_PASSWORD, new_password: SEED_PASSWORD },
      failOnStatusCode: false,
    });
    if (!restoreRes.ok()) {
      console.warn(`[forgot-password] password restore failed (${restoreRes.status()}) — global-setup will fix it next run`);
    }
  });
});
