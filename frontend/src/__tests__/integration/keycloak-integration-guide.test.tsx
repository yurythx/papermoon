import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import KeycloakIntegrationPage from "@/app/dashboard/integrations/keycloak/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

async function fillForm() {
  const user = userEvent.setup();
  await user.type(screen.getByPlaceholderText("Ex: Sistema de Chamados"), "Minha App");
  await user.type(screen.getByPlaceholderText("https://meusistema.com.br"), "https://meusistema.com.br");
  return user;
}

describe("KeycloakIntegrationPage", () => {
  it("shows the form with the generate button disabled until a base URL is entered", async () => {
    renderWithProviders(<KeycloakIntegrationPage />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /gerar guia/i })).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /gerar guia/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /criar integração/i })).toBeDisabled();
  });

  it("generates the guide and shows the real URLs + code snippet", async () => {
    renderWithProviders(<KeycloakIntegrationPage />);
    await waitFor(() => screen.getByPlaceholderText("Ex: Sistema de Chamados"));
    const user = await fillForm();
    await user.click(screen.getByRole("button", { name: /gerar guia/i }));

    await waitFor(() => {
      expect(screen.getByText("Valores da integração")).toBeInTheDocument();
    });
    expect(screen.getByDisplayValue("https://auth.papermoon.com/realms/tenant-abc123")).toBeInTheDocument();
    expect(screen.getAllByText(/next-auth/).length).toBeGreaterThan(0);
    expect(screen.getByText("Confirmado com o Keycloak agora")).toBeInTheDocument();
  });

  it("shows the empty state upfront when the platform/customer isn't set up for it", async () => {
    server.use(
      http.get("/api/proxy/client/subscriptions/keycloak-integrations/", () =>
        HttpResponse.json({
          success: true,
          data: { available: false, reason: "platform_not_configured", integrations: [] },
          error: null,
        })
      )
    );

    renderWithProviders(<KeycloakIntegrationPage />);

    await waitFor(() => {
      expect(
        screen.getByText("Integração Keycloak ainda não está disponível")
      ).toBeInTheDocument();
    });
    // Nem o formulário aparece — a checagem da conexão central vem antes de tudo.
    expect(screen.queryByPlaceholderText("Ex: Sistema de Chamados")).not.toBeInTheDocument();
  });

  it("shows a warning badge instead of the confirmed one when discovery wasn't verified", async () => {
    server.use(
      http.get("/api/proxy/client/subscriptions/keycloak-integration-guide/", () =>
        HttpResponse.json({
          success: true,
          data: {
            available: true,
            verified: false,
            issuer: "https://auth.papermoon.com/realms/tenant-abc123",
            authorization_endpoint: "https://auth.papermoon.com/realms/tenant-abc123/protocol/openid-connect/auth",
            token_endpoint: "https://auth.papermoon.com/realms/tenant-abc123/protocol/openid-connect/token",
            userinfo_endpoint: "https://auth.papermoon.com/realms/tenant-abc123/protocol/openid-connect/userinfo",
            jwks_uri: "https://auth.papermoon.com/realms/tenant-abc123/protocol/openid-connect/certs",
            end_session_endpoint: "https://auth.papermoon.com/realms/tenant-abc123/protocol/openid-connect/logout",
            client_id_suggestion: "minha-app",
            redirect_uri: "https://meusistema.com.br/oidc/callback/",
            scopes: ["openid", "profile", "email"],
            language: "django",
            package: "mozilla-django-oidc",
            install_command: "pip install mozilla-django-oidc",
            steps: ["Instale o pacote."],
            code_snippet: "OIDC_RP_CLIENT_ID = \"minha-app\"",
          },
          error: null,
        })
      )
    );

    renderWithProviders(<KeycloakIntegrationPage />);
    await waitFor(() => screen.getByPlaceholderText("Ex: Sistema de Chamados"));
    const user = await fillForm();
    await user.click(screen.getByRole("tab", { name: "Django" }));
    await user.click(screen.getByRole("button", { name: /gerar guia/i }));

    await waitFor(() => {
      expect(screen.getByText("Não confirmado — usando caminhos padrão")).toBeInTheDocument();
    });
  });

  it("lists existing integrations with a reveal-credentials action for confidential clients", async () => {
    server.use(
      http.get("/api/proxy/client/subscriptions/keycloak-integrations/", () =>
        HttpResponse.json({
          success: true,
          data: {
            available: true,
            reason: null,
            integrations: [
              {
                id: "kc-int-1",
                client_id: "sistema-chamados",
                realm: "tenant-abc123",
                app_name: "Sistema de Chamados",
                base_url: "https://chamados.com.br",
                redirect_uri: "https://chamados.com.br/api/auth/callback/keycloak",
                language: "nextjs",
                public_client: false,
                created_at: "2024-06-01T00:00:00Z",
              },
            ],
          },
          error: null,
        })
      )
    );

    const user = userEvent.setup();
    renderWithProviders(<KeycloakIntegrationPage />);

    await waitFor(() => {
      expect(screen.getByText("Minhas integrações")).toBeInTheDocument();
    });
    expect(screen.getByText("Sistema de Chamados")).toBeInTheDocument();
    expect(screen.getByText("sistema-chamados")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /ver credenciais/i }));

    await waitFor(() => {
      expect(screen.getByDisplayValue("s3cr3t-real")).toBeInTheDocument();
    });
  });

  it("does not show a reveal-credentials action for a public client", async () => {
    server.use(
      http.get("/api/proxy/client/subscriptions/keycloak-integrations/", () =>
        HttpResponse.json({
          success: true,
          data: {
            available: true,
            reason: null,
            integrations: [
              {
                id: "kc-int-2",
                client_id: "spa-publico",
                realm: "tenant-abc123",
                app_name: "SPA Público",
                base_url: "https://spa.com.br",
                redirect_uri: "https://spa.com.br/callback",
                language: "js",
                public_client: true,
                created_at: "2024-06-01T00:00:00Z",
              },
            ],
          },
          error: null,
        })
      )
    );

    renderWithProviders(<KeycloakIntegrationPage />);

    await waitFor(() => {
      expect(screen.getByText("SPA Público")).toBeInTheDocument();
    });
    expect(screen.getByText("Público (PKCE)")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /ver credenciais/i })).not.toBeInTheDocument();
  });

  it("creates a real client after confirming, and shows the real client_secret", async () => {
    const user = userEvent.setup();
    renderWithProviders(<KeycloakIntegrationPage />);
    await waitFor(() => screen.getByPlaceholderText("Ex: Sistema de Chamados"));
    await fillForm();

    await user.click(screen.getByRole("button", { name: /criar integração/i }));

    await waitFor(() => {
      expect(screen.getByText("Criar integração de verdade?")).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: "Criar" }));

    await waitFor(() => {
      expect(screen.getByText("Integração criada com sucesso")).toBeInTheDocument();
    });
    expect(screen.getByDisplayValue("minha-app")).toBeInTheDocument();
    expect(screen.getByDisplayValue("s3cr3t-real")).toBeInTheDocument();
  });

  it("closes the confirm dialog without showing a success panel when creation fails", async () => {
    server.use(
      http.post("/api/proxy/client/subscriptions/keycloak-integrations/", () =>
        HttpResponse.json(
          {
            success: false,
            data: null,
            error: {
              code: "platform_not_configured",
              message: "Integração com o Keycloak ainda não está disponível para sua conta.",
              details: [],
            },
          },
          { status: 409 }
        )
      )
    );

    const user = userEvent.setup();
    renderWithProviders(<KeycloakIntegrationPage />);
    await waitFor(() => screen.getByPlaceholderText("Ex: Sistema de Chamados"));
    await fillForm();

    await user.click(screen.getByRole("button", { name: /criar integração/i }));
    await waitFor(() => screen.getByText("Criar integração de verdade?"));
    await user.click(screen.getByRole("button", { name: "Criar" }));

    // O dialog fecha e nenhum painel de resultado "criado com sucesso" aparece.
    await waitFor(() => {
      expect(screen.queryByText("Criar integração de verdade?")).not.toBeInTheDocument();
    });
    expect(screen.queryByText("Integração criada com sucesso")).not.toBeInTheDocument();
  });
});
