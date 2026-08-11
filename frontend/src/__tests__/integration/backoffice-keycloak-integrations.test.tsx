import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
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
