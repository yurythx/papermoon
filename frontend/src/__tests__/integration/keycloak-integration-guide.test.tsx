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
  it("shows the form with the generate button disabled until a base URL is entered", () => {
    renderWithProviders(<KeycloakIntegrationPage />);
    expect(screen.getByRole("button", { name: /gerar guia/i })).toBeDisabled();
  });

  it("generates the guide and shows the real URLs + code snippet", async () => {
    renderWithProviders(<KeycloakIntegrationPage />);
    const user = await fillForm();
    await user.click(screen.getByRole("button", { name: /gerar guia/i }));

    await waitFor(() => {
      expect(screen.getByText("Valores da integração")).toBeInTheDocument();
    });
    expect(screen.getByDisplayValue("https://auth.papermoon.com/realms/tenant-abc123")).toBeInTheDocument();
    expect(screen.getAllByText(/next-auth/).length).toBeGreaterThan(0);
    expect(screen.getByText("Confirmado com o Keycloak agora")).toBeInTheDocument();
  });

  it("shows the empty state when the customer has no active Keycloak service access", async () => {
    server.use(
      http.get("/api/proxy/client/subscriptions/keycloak-integration-guide/", () =>
        HttpResponse.json({ success: true, data: { available: false }, error: null })
      )
    );

    renderWithProviders(<KeycloakIntegrationPage />);
    const user = await fillForm();
    await user.click(screen.getByRole("button", { name: /gerar guia/i }));

    await waitFor(() => {
      expect(
        screen.getByText("Integração Keycloak ainda não está disponível")
      ).toBeInTheDocument();
    });
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
    const user = await fillForm();
    await user.click(screen.getByRole("tab", { name: "Django" }));
    await user.click(screen.getByRole("button", { name: /gerar guia/i }));

    await waitFor(() => {
      expect(screen.getByText("Não confirmado — usando caminhos padrão")).toBeInTheDocument();
    });
  });
});
