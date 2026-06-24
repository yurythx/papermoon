import { test, expect } from "@playwright/test";

test.describe("Landing page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("renders hero section with headline", async ({ page }) => {
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  });

  test("nav links are visible", async ({ page }) => {
    await expect(page.getByRole("link", { name: /papermoon/i }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Entrar", exact: true })).toBeVisible();
  });

  test("nav Contato link points to #contato", async ({ page }) => {
    const link = page.locator("nav a[href='/#contato']");
    await expect(link).toBeVisible();
    await expect(link).toHaveText(/contato/i);
  });

  test("nav has Sobre link", async ({ page }) => {
    await expect(page.locator("nav a[href='/sobre']")).toBeVisible();
  });

  test("services section is visible with key services", async ({ page }) => {
    const section = page.locator("#servicos");
    await section.scrollIntoViewIfNeeded();
    await expect(section).toBeVisible();
    await expect(section.getByText(/GLPI/i).first()).toBeVisible();
    await expect(section.getByText(/Zabbix/i).first()).toBeVisible();
  });

  test("como funciona section has 3 steps", async ({ page }) => {
    const section = page.locator("#como-funciona");
    await section.scrollIntoViewIfNeeded();
    await expect(section.getByText("01").first()).toBeVisible();
    await expect(section.getByText("02").first()).toBeVisible();
    await expect(section.getByText("03").first()).toBeVisible();
  });

  test("FAQ section renders and expands", async ({ page }) => {
    const section = page.locator("#faq");
    await section.scrollIntoViewIfNeeded();
    await expect(section).toBeVisible();
    // First question should be visible
    const firstQuestion = section.getByRole("button").first();
    await expect(firstQuestion).toBeVisible();
    await firstQuestion.click();
    // After clicking, some answer text should appear
    await expect(section.locator("p").first()).toBeVisible();
  });

  test("contato section visible with email and WhatsApp links", async ({ page }) => {
    await page.locator("#contato").scrollIntoViewIfNeeded();
    await expect(page.locator("a[href='mailto:contato@papermoon.com.br']").first()).toBeVisible();
    await expect(page.locator("a[href*='wa.me']").first()).toBeVisible();
  });

  test("footer has Sobre and Termos links", async ({ page }) => {
    const footer = page.locator("footer");
    await footer.scrollIntoViewIfNeeded();
    await expect(footer.getByRole("link", { name: /sobre/i })).toBeVisible();
    await expect(footer.getByRole("link", { name: /termos/i })).toBeVisible();
  });

  test("hero CTA Entrar navigates to login", async ({ page }) => {
    const loginLink = page.getByRole("link", { name: "Entrar", exact: true });
    await expect(loginLink).toHaveAttribute("href", "/login");
  });
});

test.describe("Sobre page", () => {
  test("renders with main sections", async ({ page }) => {
    await page.goto("/sobre");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText("10+").first()).toBeVisible();
  });

  test("has contact CTA", async ({ page }) => {
    await page.goto("/sobre");
    await expect(page.locator("a[href='mailto:contato@papermoon.com.br']")).toBeVisible();
  });

  test("has link back to home", async ({ page }) => {
    await page.goto("/sobre");
    await expect(page.locator("a[href='/']").first()).toBeVisible();
  });
});

test.describe("Service pages", () => {
  test("GLPI service page renders", async ({ page }) => {
    await page.goto("/servicos/glpi");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/GLPI/i).first()).toBeVisible();
  });

  test("redes service page renders", async ({ page }) => {
    await page.goto("/servicos/redes");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/Redes corporativas/i).first()).toBeVisible();
  });

  test("cabeamento service page renders", async ({ page }) => {
    await page.goto("/servicos/cabeamento");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/Cat/i).first()).toBeVisible();
  });

  test("backup service page renders", async ({ page }) => {
    await page.goto("/servicos/backup");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/backup/i).first()).toBeVisible();
  });

  test("service page has contact CTA", async ({ page }) => {
    await page.goto("/servicos/glpi");
    await page.locator("#contato").scrollIntoViewIfNeeded();
    await expect(page.locator("a[href='mailto:contato@papermoon.com.br']")).toBeVisible();
  });

  test("service breadcrumb points to /servicos", async ({ page }) => {
    await page.goto("/servicos/zabbix");
    // First link to /servicos is the top breadcrumb; the second is "Ver todos" at the bottom
    const breadcrumb = page.locator("a[href='/servicos']").first();
    await expect(breadcrumb).toBeVisible();
    await expect(breadcrumb).toHaveText(/todos os serviços/i);
  });

  test("TrueNAS service page renders", async ({ page }) => {
    await page.goto("/servicos/truenas");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/TrueNAS/i).first()).toBeVisible();
  });

  test("TrueNAS page shows ZFS mention", async ({ page }) => {
    await page.goto("/servicos/truenas");
    await expect(page.getByText(/ZFS/i).first()).toBeVisible();
  });

  test("whatsapp-api service page renders key sections", async ({ page }) => {
    await page.goto("/servicos/whatsapp-api");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/Como funciona/i).first()).toBeVisible();
    await expect(page.getByText(/Funcionalidades/i).first()).toBeVisible();
  });

  test("service page shows 'Sobre o serviço' section with origin text and differentials", async ({ page }) => {
    await page.goto("/servicos/chatwoot");
    const heading = page.getByText("O que é e como surgiu");
    await heading.scrollIntoViewIfNeeded();
    await expect(heading).toBeVisible();
    await expect(page.getByText("O diferencial na prática").first()).toBeVisible();
    // Differential bullets are rendered
    await expect(page.getByText(/open-source e auto-hospedado/i).first()).toBeVisible();
  });

  test("service page 'Sobre o serviço' section works for physical services too", async ({ page }) => {
    await page.goto("/servicos/cabeamento");
    await expect(page.getByText("O que é e como surgiu").first()).toBeVisible();
    await expect(page.getByText("O diferencial na prática").first()).toBeVisible();
  });

  test("service page shows responsibilities section", async ({ page }) => {
    await page.goto("/servicos/glpi");
    const section = page.getByText("O que é de quem?");
    await section.scrollIntoViewIfNeeded();
    await expect(section).toBeVisible();
    await expect(page.getByText("PaperMoon faz").first()).toBeVisible();
    await expect(page.getByText("Sua responsabilidade").first()).toBeVisible();
  });

  test("service page gallery section shows placeholder when no CMS images", async ({ page }) => {
    await page.goto("/servicos/zabbix");
    // Gallery section is always visible — heading is always present
    await expect(page.getByText("Como o serviço funciona").first()).toBeVisible();
    // Without CMS images, placeholder cards appear instead of real screenshots
    await expect(page.getByText(/Capturas aguardando liberação/i).first()).toBeVisible();
    // The lightbox hint only appears when real images exist
    await expect(page.getByText(/Clique em qualquer imagem/i)).toHaveCount(0);
  });

  test("service page shows prerequisites section", async ({ page }) => {
    await page.goto("/servicos/glpi");
    const section = page.getByText("Pré-requisitos técnicos");
    await section.scrollIntoViewIfNeeded();
    await expect(section).toBeVisible();
    await expect(page.getByText("Infraestrutura necessária")).toBeVisible();
  });

  test("service page hero does not show fixed delivery time badge", async ({ page }) => {
    await page.goto("/servicos/whatsapp-api");
    await expect(page.getByText(/Entrega em/i)).toHaveCount(0);
  });

  test("service page outros servicos section links to other slugs", async ({ page }) => {
    await page.goto("/servicos/glpi");
    const section = page.getByText("Outros serviços");
    await section.scrollIntoViewIfNeeded();
    await expect(section).toBeVisible();
    // Should have at least one other service link
    const links = page.locator("a[href^='/servicos/']");
    await expect(links.first()).toBeVisible();
  });

  test("plone service page renders", async ({ page }) => {
    await page.goto("/servicos/plone");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/Plone/i).first()).toBeVisible();
  });

  test("keycloak service page renders", async ({ page }) => {
    await page.goto("/servicos/keycloak");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/Keycloak/i).first()).toBeVisible();
  });

  test("tailscale service page renders", async ({ page }) => {
    await page.goto("/servicos/tailscale");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/Tailscale/i).first()).toBeVisible();
  });

  test("twenty-crm service page renders", async ({ page }) => {
    await page.goto("/servicos/twenty-crm");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/Twenty/i).first()).toBeVisible();
  });

  test("papermark service page renders", async ({ page }) => {
    await page.goto("/servicos/papermark");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/Papermark/i).first()).toBeVisible();
  });

  test("crowdsec service page renders", async ({ page }) => {
    await page.goto("/servicos/crowdsec");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/CrowdSec/i).first()).toBeVisible();
  });

  test("all services appear in landing page vitrine", async ({ page }) => {
    await page.goto("/");
    const servicos = page.locator("#servicos");
    await servicos.scrollIntoViewIfNeeded();
    // digital / software services
    await expect(servicos.getByText(/Plone/i).first()).toBeVisible();
    await expect(servicos.getByText(/Keycloak/i).first()).toBeVisible();
    await expect(servicos.getByText(/Tailscale/i).first()).toBeVisible();
    await expect(servicos.getByText(/CrowdSec/i).first()).toBeVisible();
    await expect(servicos.getByText(/Chatwoot/i).first()).toBeVisible();
    await expect(servicos.getByText(/n8n/i).first()).toBeVisible();
    // physical / infra services added to vitrine
    await expect(servicos.getByText(/Evolution API/i).first()).toBeVisible();
    await expect(servicos.getByText(/Redes corporativas/i).first()).toBeVisible();
    await expect(servicos.getByText(/Cabeamento estruturado/i).first()).toBeVisible();
    await expect(servicos.getByText(/Manutenção de servidores/i).first()).toBeVisible();
    await expect(servicos.getByText(/Backup corporativo/i).first()).toBeVisible();
  });

  test("landing page catalog link points to /servicos", async ({ page }) => {
    await page.goto("/");
    const link = page.getByRole("link", { name: /ver catálogo completo por categoria/i });
    await link.scrollIntoViewIfNeeded();
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute("href", "/servicos");
  });
});

test.describe("/servicos index page", () => {
  test("renders heading and category sections", async ({ page }) => {
    await page.goto("/servicos");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/Comunicação/i).first()).toBeVisible();
    await expect(page.getByText(/Infraestrutura/i).first()).toBeVisible();
    await expect(page.getByText(/Segurança e Identidade/i).first()).toBeVisible();
  });

  test("shows all service cards with links", async ({ page }) => {
    await page.goto("/servicos");
    // Spot-check a few services from different categories
    await expect(page.getByRole("link", { name: /chatwoot/i }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: /proxmox/i }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: /keycloak/i }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: /tailscale/i }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: /backup/i }).first()).toBeVisible();
  });

  test("card links point to individual service pages", async ({ page }) => {
    await page.goto("/servicos");
    const glpiLink = page.locator("a[href='/servicos/glpi']").first();
    await expect(glpiLink).toBeVisible();
    await glpiLink.click();
    await expect(page).toHaveURL("/servicos/glpi");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  });

  test("back link returns to landing page services section", async ({ page }) => {
    await page.goto("/servicos");
    const back = page.getByRole("link", { name: /voltar para o início/i });
    await expect(back).toBeVisible();
    await expect(back).toHaveAttribute("href", "/#servicos");
  });
});
