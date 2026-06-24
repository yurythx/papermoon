import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import LicensesPage from "@/app/dashboard/licenses/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/dashboard/licenses",
  useSearchParams: () => ({ get: () => null }),
}));

describe("LicensesPage", () => {
  it("renders license cards after loading", async () => {
    renderWithProviders(<LicensesPage />);

    await waitFor(() => {
      expect(screen.getByText("Atendimento WhatsApp")).toBeInTheDocument();
    });

    expect(screen.getByText("lic-abc123")).toBeInTheDocument();
    expect(screen.getByText("Ativo")).toBeInTheDocument();
  });

  it("shows service chips on the card", async () => {
    renderWithProviders(<LicensesPage />);
    await waitFor(() => screen.getByText("Atendimento WhatsApp"));
    expect(screen.getByText("n8n")).toBeInTheDocument();
  });

  it("shows empty state when there are no licenses", async () => {
    server.use(
      http.get("/api/proxy/client/licenses/", () =>
        HttpResponse.json({ success: true, data: { count: 0, next: null, previous: null, results: [] }, error: null })
      )
    );

    renderWithProviders(<LicensesPage />);
    await waitFor(() => {
      expect(screen.getByText(/nenhuma licença ativa/i)).toBeInTheDocument();
    });
  });

  it("shows expiring soon warning when days_remaining <= 30", async () => {
    // Use a future date so TimeProgress can compute remaining days
    const validUntil = new Date(Date.now() + 7.5 * 24 * 60 * 60 * 1000).toISOString();
    const createdAt = new Date(Date.now() - 22.5 * 24 * 60 * 60 * 1000).toISOString();

    server.use(
      http.get("/api/proxy/client/licenses/", () =>
        HttpResponse.json({
          success: true,
          data: {
            count: 1, next: null, previous: null,
            results: [{
              id: "lic2", key: "lic-xyz", status: "active",
              valid_from: createdAt, valid_until: validUntil,
              days_remaining: 7, product_name: "GLPI Helpdesk", product_slug: "pro",
              subscription_id: "sub1", subscription_status: "active",
              billing_cycle: "monthly", amount: "399.00",
              services: [], created_at: createdAt,
            }],
          },
          error: null,
        })
      )
    );

    renderWithProviders(<LicensesPage />);
    await waitFor(() => screen.getByText("GLPI Helpdesk"));
    // TimeProgress renders "X dias restantes" label
    expect(screen.getByText(/\d+ dias restantes/i)).toBeInTheDocument();
  });
});
