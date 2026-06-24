import { defineConfig, devices } from "@playwright/test";

const isCI = !!process.env.CI;

export default defineConfig({
  globalSetup: require.resolve("./e2e/global-setup.ts"),
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  retries: isCI ? 2 : 1,
  workers: 1,
  reporter: [["html", { open: "never" }], ["list"]],

  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },

  webServer: isCI || process.env.PLAYWRIGHT_BASE_URL
    ? undefined
    : {
        command: "npm run start",
        url: "http://localhost:3000",
        reuseExistingServer: true,
        timeout: 60_000,
      },

  projects: [
    // Auth setup — runs once, saves cookies to .auth/
    {
      name: "setup",
      testMatch: "**/auth.setup.ts",
    },
    {
      name: "setup-admin",
      testMatch: "**/admin.setup.ts",
    },

    // Owner-authenticated dashboard tests
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        storageState: ".auth/owner.json",
      },
      dependencies: ["setup"],
      testIgnore: [
        "**/auth.setup.ts",
        "**/admin.setup.ts",
        "**/auth.spec.ts",
        "**/landing.spec.ts",
        "**/forgot-password.spec.ts",
        "**/backoffice*.spec.ts",
      ],
    },

    // Admin-authenticated backoffice tests
    {
      name: "chromium-admin",
      use: {
        ...devices["Desktop Chrome"],
        storageState: ".auth/admin.json",
      },
      dependencies: ["setup-admin"],
      testMatch: ["**/backoffice*.spec.ts"],
    },

    // Public / no-auth: auth flow, landing, password reset
    {
      name: "chromium-no-auth",
      use: { ...devices["Desktop Chrome"] },
      testMatch: [
        "**/auth.spec.ts",
        "**/landing.spec.ts",
        "**/forgot-password.spec.ts",
      ],
    },
  ],
});
