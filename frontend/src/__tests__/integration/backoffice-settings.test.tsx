import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import BackofficeSettingsPage from "@/app/backoffice/settings/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/backoffice/settings",
}));

describe("BackofficeSettingsPage", () => {
  it("renders both the staff SSO card and the central Keycloak connection card", async () => {
    renderWithProviders(<BackofficeSettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("Login via Keycloak (SSO)")).toBeInTheDocument();
    });
    expect(screen.getByText("Conexão com o Keycloak (provisionamento)")).toBeInTheDocument();
  });

  it("saves the SSO card and never echoes the client secret back", async () => {
    const user = userEvent.setup();
    renderWithProviders(<BackofficeSettingsPage />);

    await waitFor(() => {
      expect(screen.getByLabelText("Issuer (URL do realm)")).toBeInTheDocument();
    });

    await user.type(
      screen.getByLabelText("Issuer (URL do realm)"),
      "https://keycloak.example.com/realms/papermoon-staff"
    );
    await user.type(screen.getByLabelText("Client ID"), "papermoon-backoffice");
    await user.type(screen.getByLabelText("Client Secret"), "s3cr3t-staff");

    const ssoCard = screen.getByText("Login via Keycloak (SSO)").closest("div.space-y-5");
    expect(ssoCard).not.toBeNull();
    await user.click(within(ssoCard as HTMLElement).getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      expect(within(ssoCard as HTMLElement).getByText(/Última atualização/)).toBeInTheDocument();
    });

    expect(screen.queryByText("s3cr3t-staff")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Client Secret")).toHaveValue("");
    expect(
      within(ssoCard as HTMLElement).getByPlaceholderText("•••••••• (deixe em branco para manter)")
    ).toBeInTheDocument();
  });

  it("shows the connectivity banner when the SSO test button is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<BackofficeSettingsPage />);

    await waitFor(() => {
      expect(screen.getByLabelText("Issuer (URL do realm)")).toBeInTheDocument();
    });
    await user.type(
      screen.getByLabelText("Issuer (URL do realm)"),
      "https://keycloak.example.com/realms/papermoon-staff"
    );

    const ssoCard = screen.getByText("Login via Keycloak (SSO)").closest("div.space-y-5");
    await user.click(within(ssoCard as HTMLElement).getByRole("button", { name: "Testar conexão" }));

    await waitFor(() => {
      expect(
        within(ssoCard as HTMLElement).getByText("Conectou e o discovery document é válido.")
      ).toBeInTheDocument();
    });
  });

  it("saves the central Keycloak connection card and never echoes the admin token", async () => {
    const user = userEvent.setup();
    renderWithProviders(<BackofficeSettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("Conexão com o Keycloak (provisionamento)")).toBeInTheDocument();
    });

    await user.type(screen.getByLabelText("URL da API (base do Keycloak)"), "https://auth.papermoon.com");
    await user.type(screen.getByLabelText("Admin token"), "s3cr3t-admin-token");

    const kcCard = screen.getByText("Conexão com o Keycloak (provisionamento)").closest("div.space-y-5");
    expect(kcCard).not.toBeNull();
    await user.click(within(kcCard as HTMLElement).getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      expect(within(kcCard as HTMLElement).getByText(/Última atualização/)).toBeInTheDocument();
    });

    expect(screen.queryByText("s3cr3t-admin-token")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Admin token")).toHaveValue("");
    expect(
      within(kcCard as HTMLElement).getByPlaceholderText("•••••••• (deixe em branco para manter)")
    ).toBeInTheDocument();
  });

  it("shows the connectivity banner when the Keycloak connection test button is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<BackofficeSettingsPage />);

    await waitFor(() => {
      expect(screen.getByLabelText("URL da API (base do Keycloak)")).toBeInTheDocument();
    });
    await user.type(screen.getByLabelText("URL da API (base do Keycloak)"), "https://auth.papermoon.com");

    const kcCard = screen.getByText("Conexão com o Keycloak (provisionamento)").closest("div.space-y-5");
    await user.click(within(kcCard as HTMLElement).getByRole("button", { name: "Testar conexão" }));

    await waitFor(() => {
      expect(
        within(kcCard as HTMLElement).getByText(
          "Conectou e o token foi aceito — 3 realm(s) visível(is)."
        )
      ).toBeInTheDocument();
    });
  });

  it("shows an error banner from the API when saving the Keycloak connection fails validation", async () => {
    server.use(
      http.patch("/api/proxy/admin/keycloak-connection/", () =>
        HttpResponse.json(
          {
            success: false,
            data: null,
            error: {
              code: "validation_error",
              message: "api_url e admin_token são obrigatórios para ativar a conexão.",
              details: [],
            },
          },
          { status: 400 }
        )
      )
    );

    const user = userEvent.setup();
    renderWithProviders(<BackofficeSettingsPage />);

    await waitFor(() => {
      expect(screen.getByText("Conexão com o Keycloak (provisionamento)")).toBeInTheDocument();
    });
    await user.type(screen.getByLabelText("URL da API (base do Keycloak)"), "https://auth.papermoon.com");
    await user.type(screen.getByLabelText("Admin token"), "tok");

    const kcCard = screen.getByText("Conexão com o Keycloak (provisionamento)").closest("div.space-y-5");
    await user.click(within(kcCard as HTMLElement).getByRole("button", { name: "Salvar" }));

    // A chamada falhou — a conexão continua desativada, sem "Última atualização".
    await waitFor(() => {
      expect(
        within(kcCard as HTMLElement).queryByText(/Última atualização/)
      ).not.toBeInTheDocument();
    });
  });
});
