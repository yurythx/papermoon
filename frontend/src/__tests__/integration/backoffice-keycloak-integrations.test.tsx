import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import BackofficeKeycloakIntegrationsPage from "@/app/backoffice/integrations/keycloak/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/backoffice/integrations/keycloak",
}));

describe("BackofficeKeycloakIntegrationsPage", () => {
  it("validates an arbitrary issuer without picking any customer", async () => {
    const user = userEvent.setup();
    renderWithProviders(<BackofficeKeycloakIntegrationsPage />);

    await user.type(
      screen.getByPlaceholderText("https://keycloak.exemplo.com.br/realms/algum-realm"),
      "https://auth.cliente-externo.com.br/realms/algum-realm"
    );
    await user.click(screen.getByRole("button", { name: "Validar" }));

    await waitFor(() => {
      expect(
        screen.getByText("Discovery document confirmado — o issuer é válido.")
      ).toBeInTheDocument();
    });
  });

  it("explains what each endpoint is for and where to put it", async () => {
    const user = userEvent.setup();
    renderWithProviders(<BackofficeKeycloakIntegrationsPage />);

    await user.type(
      screen.getByPlaceholderText("https://keycloak.exemplo.com.br/realms/algum-realm"),
      "https://auth.cliente-externo.com.br/realms/algum-realm"
    );
    await user.click(screen.getByRole("button", { name: "Validar" }));

    await waitFor(() => screen.getByText("Authorization endpoint"));
    expect(
      screen.getByText(/Pra onde o navegador do usuário é redirecionado pra fazer login/)
    ).toBeInTheDocument();
    expect(screen.getAllByText("Pra que serve:").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Onde colocar:").length).toBeGreaterThan(0);
  });

  it("generates the manual Keycloak admin console fields for a confidential client", async () => {
    const user = userEvent.setup();
    renderWithProviders(<BackofficeKeycloakIntegrationsPage />);

    await user.type(
      screen.getByPlaceholderText("Ex: Portal do Fornecedor"),
      "Portal do Fornecedor"
    );
    await user.type(
      screen.getByPlaceholderText("https://sistemadocliente.com.br/auth/callback"),
      "https://fornecedor.com.br/auth/callback"
    );

    await waitFor(() => screen.getByText("1. General settings"));
    expect(screen.getByText("portal-do-fornecedor")).toBeInTheDocument();
    expect(screen.getAllByText("https://fornecedor.com.br").length).toBeGreaterThan(0);
    expect(
      screen.getByText("https://fornecedor.com.br/auth/callback")
    ).toBeInTheDocument();
    // Confidencial é o default — Client authentication deve estar "On".
    const authRow = screen
      .getByText("Client authentication")
      .closest("div.flex.items-start.justify-between");
    expect(within(authRow as HTMLElement).getByText("On")).toBeInTheDocument();
  });

  it("switches the manual setup fields when the client type is public", async () => {
    const user = userEvent.setup();
    renderWithProviders(<BackofficeKeycloakIntegrationsPage />);

    await user.type(screen.getByPlaceholderText("Ex: Portal do Fornecedor"), "SPA Publica");
    await user.type(
      screen.getByPlaceholderText("https://sistemadocliente.com.br/auth/callback"),
      "https://spa.com.br/callback"
    );
    await user.click(screen.getByRole("button", { name: /Público \(SPA/i }));

    await waitFor(() => screen.getByText("1. General settings"));
    // Client authentication vira "Off" pra client público.
    const authRow = screen
      .getByText("Client authentication")
      .closest("div.flex.items-start.justify-between");
    expect(within(authRow as HTMLElement).getByText("Off")).toBeInTheDocument();
    // Web origins passa a ser preenchido (necessário pro CORS de um SPA).
    const originsRow = screen.getByText("Web origins").closest("div.flex.items-start.justify-between");
    expect(within(originsRow as HTMLElement).getByText("https://spa.com.br")).toBeInTheDocument();
  });

  it("generates a code example after validating an issuer and picking a language", async () => {
    const user = userEvent.setup();
    renderWithProviders(<BackofficeKeycloakIntegrationsPage />);

    // Passo 1: valida o issuer no primeiro card.
    await user.type(
      screen.getByPlaceholderText("https://keycloak.exemplo.com.br/realms/algum-realm"),
      "https://auth.cliente-externo.com.br/realms/algum-realm"
    );
    await user.click(screen.getByRole("button", { name: "Validar" }));
    await waitFor(() =>
      screen.getByText("Discovery document confirmado — o issuer é válido.")
    );

    // Passo 2: preenche o gerador de campos manuais — libera a seção 4.
    await user.type(screen.getByPlaceholderText("Ex: Portal do Fornecedor"), "Portal do Fornecedor");
    await user.type(
      screen.getByPlaceholderText("https://sistemadocliente.com.br/auth/callback"),
      "https://fornecedor.com.br/auth/callback"
    );
    await waitFor(() => screen.getByText("4. Exemplo de código"));

    // O aviso de "valide um issuer" não deve aparecer — já foi validado no passo 1.
    expect(
      screen.queryByText(/Valide um issuer no card/i)
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Gerar exemplo" }));

    await waitFor(() => {
      expect(screen.getByText(/Código \(next-auth\)/)).toBeInTheDocument();
    });
    // "portal-do-fornecedor" aparece tanto no campo Client ID (passo 1) quanto
    // dentro do exemplo de código gerado (passo 4).
    expect(screen.getAllByText(/portal-do-fornecedor/).length).toBeGreaterThanOrEqual(2);
  });

  it("warns when trying to generate a code example without a validated issuer", async () => {
    const user = userEvent.setup();
    renderWithProviders(<BackofficeKeycloakIntegrationsPage />);

    await user.type(screen.getByPlaceholderText("Ex: Portal do Fornecedor"), "Portal");
    await user.type(
      screen.getByPlaceholderText("https://sistemadocliente.com.br/auth/callback"),
      "https://fornecedor.com.br/callback"
    );

    await waitFor(() => screen.getByText("4. Exemplo de código"));
    expect(screen.getByText(/Valide um issuer no card/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Gerar exemplo" })).toBeDisabled();
  });

  it("does not show the integration manager until a customer is selected", async () => {
    renderWithProviders(<BackofficeKeycloakIntegrationsPage />);
    expect(screen.getByText("Nenhum cliente selecionado")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /criar integração/i })).not.toBeInTheDocument();
  });

  it("shows the integration manager for the selected customer", async () => {
    const user = userEvent.setup();
    renderWithProviders(<BackofficeKeycloakIntegrationsPage />);

    await waitFor(() => {
      expect(screen.getByText("Acme Ltda")).toBeInTheDocument();
    });
    await user.selectOptions(screen.getByLabelText("Cliente"), "c1");

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /criar integração/i })).toBeInTheDocument();
    });
  });

  it("shows a staff-specific reason when the platform isn't configured", async () => {
    server.use(
      http.get("/api/proxy/admin/customers/:customerId/keycloak-integrations/", () =>
        HttpResponse.json({
          success: true,
          data: { available: false, reason: "platform_not_configured", integrations: [] },
          error: null,
        })
      )
    );

    const user = userEvent.setup();
    renderWithProviders(<BackofficeKeycloakIntegrationsPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));
    await user.selectOptions(screen.getByLabelText("Cliente"), "c1");

    await waitFor(() => {
      expect(
        screen.getByText("Integração Keycloak não está disponível pra esse cliente")
      ).toBeInTheDocument();
    });
    expect(
      screen.getByText(/conexão central do PaperMoon com o Keycloak não está configurada/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ir pra Configurações" })).toHaveAttribute(
      "href",
      "/backoffice/settings"
    );
  });

  it("creates a real integration on behalf of the selected customer", async () => {
    const user = userEvent.setup();
    renderWithProviders(<BackofficeKeycloakIntegrationsPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));
    await user.selectOptions(screen.getByLabelText("Cliente"), "c1");
    await waitFor(() => screen.getByRole("button", { name: /criar integração/i }));

    await user.type(screen.getByPlaceholderText("Ex: Sistema de Chamados"), "Sistema do Cliente");
    await user.type(
      screen.getByPlaceholderText("https://meusistema.com.br"),
      "https://sistema-cliente.com.br"
    );
    await user.click(screen.getByRole("button", { name: /criar integração/i }));
    await waitFor(() => screen.getByText("Criar integração de verdade?"));
    await user.click(screen.getByRole("button", { name: "Criar" }));

    await waitFor(() => {
      expect(screen.getByText("Integração criada com sucesso")).toBeInTheDocument();
    });
    expect(screen.getByDisplayValue("sistema-do-cliente")).toBeInTheDocument();
  });
});
