import { screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import InvoicesPage from "@/app/dashboard/invoices/page";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/dashboard/invoices",
}));

describe("Client InvoicesPage", () => {
  it("renders invoices list", async () => {
    renderWithProviders(<InvoicesPage />);
    await waitFor(() => expect(screen.getAllByRole("row").length).toBeGreaterThan(1));
  });

  it("shows status badges", async () => {
    renderWithProviders(<InvoicesPage />);
    await waitFor(() => {
      expect(screen.getByText("Pago")).toBeTruthy();
      expect(screen.getByText("Pendente")).toBeTruthy();
      expect(screen.getByText("Vencida")).toBeTruthy();
    });
  });

  it("shows Pagar link for pending invoice with payment_url", async () => {
    renderWithProviders(<InvoicesPage />);
    await waitFor(() => {
      const link = screen.getByRole("link", { name: /pagar/i });
      expect(link).toBeTruthy();
      expect((link as HTMLAnchorElement).href).toContain("asaas.com");
    });
  });

  it("does not show Pagar for paid invoices", async () => {
    renderWithProviders(<InvoicesPage />);
    await waitFor(() => screen.getByText("Pago"));
    const payLinks = screen.queryAllByRole("link", { name: /pagar/i });
    expect(payLinks.length).toBe(1); // only the pending one
  });

  it("shows total count", async () => {
    renderWithProviders(<InvoicesPage />);
    await waitFor(() => expect(screen.getByText(/3 faturas/)).toBeTruthy());
  });

  it("shows empty state when no invoices", async () => {
    const { http, HttpResponse } = await import("msw");
    const { server } = await import("../mocks/server");
    server.use(
      http.get("/api/proxy/client/invoices/", () =>
        HttpResponse.json({ success: true, data: { count: 0, next: null, previous: null, results: [] }, error: null })
      )
    );
    renderWithProviders(<InvoicesPage />);
    await waitFor(() => expect(screen.getByText(/Nenhuma fatura encontrada/)).toBeTruthy());
  });

  it("status filter buttons render", async () => {
    renderWithProviders(<InvoicesPage />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Todas" })).toBeTruthy();
      expect(screen.getByRole("button", { name: "Pendentes" })).toBeTruthy();
      expect(screen.getByRole("button", { name: "Pagas" })).toBeTruthy();
    });
  });

  it("clicking filter button does not throw", async () => {
    renderWithProviders(<InvoicesPage />);
    await waitFor(() => screen.getByRole("button", { name: "Pagas" }));
    expect(() => fireEvent.click(screen.getByRole("button", { name: "Pagas" }))).not.toThrow();
  });

  it("shows Exportar CSV button", async () => {
    renderWithProviders(<InvoicesPage />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /exportar csv/i })).toBeTruthy()
    );
  });

  it("Exportar CSV button is enabled", async () => {
    renderWithProviders(<InvoicesPage />);
    await waitFor(() => {
      const btn = screen.getByRole("button", { name: /exportar csv/i });
      expect((btn as HTMLButtonElement).disabled).toBe(false);
    });
  });

  it("shows dunning danger banner when overdue invoice exists far past due", async () => {
    renderWithProviders(<InvoicesPage />);
    // The mock returns an overdue invoice with due_date 2024-05-01 (>7 days ago)
    await waitFor(() => {
      expect(screen.getByText(/suspensão iminente/i)).toBeInTheDocument();
    });
  });
});
