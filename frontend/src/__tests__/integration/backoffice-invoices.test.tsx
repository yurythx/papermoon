import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import BackofficeInvoicesPage from "@/app/backoffice/invoices/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/backoffice/invoices",
  useSearchParams: () => ({ get: () => null }),
}));

describe("BackofficeInvoicesPage", () => {
  it("renders invoice list after loading", async () => {
    renderWithProviders(<BackofficeInvoicesPage />);

    await waitFor(() => {
      expect(screen.getByText("Acme Ltda")).toBeInTheDocument();
      expect(screen.getByText("Mega Corp")).toBeInTheDocument();
    });
  });

  it("shows status badges for each invoice", async () => {
    renderWithProviders(<BackofficeInvoicesPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    // Use getAllByText because labels also appear in the filter <option> elements
    expect(screen.getAllByText("Pago").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Vencido").length).toBeGreaterThanOrEqual(1);
  });

  it("shows formatted currency amounts", async () => {
    renderWithProviders(<BackofficeInvoicesPage />);

    await waitFor(() => {
      expect(screen.getByText(/R\$\s*199/)).toBeInTheDocument();
      expect(screen.getByText(/R\$\s*399/)).toBeInTheDocument();
    });
  });

  it("shows remove button for each invoice", async () => {
    renderWithProviders(<BackofficeInvoicesPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    const removeBtns = screen.getAllByRole("button", { name: /remover/i });
    expect(removeBtns.length).toBeGreaterThanOrEqual(2);
  });

  it("opens confirmation dialog when clicking remove", async () => {
    renderWithProviders(<BackofficeInvoicesPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    const [firstRemoveBtn] = screen.getAllByRole("button", { name: /remover/i });
    fireEvent.click(firstRemoveBtn);

    await waitFor(() => {
      expect(screen.getByText("Remover fatura")).toBeInTheDocument();
      expect(screen.getByText(/soft-delete/i)).toBeInTheDocument();
    });
  });

  it("closes dialog on cancel", async () => {
    renderWithProviders(<BackofficeInvoicesPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    const [firstRemoveBtn] = screen.getAllByRole("button", { name: /remover/i });
    fireEvent.click(firstRemoveBtn);

    await waitFor(() => screen.getByText("Remover fatura"));

    fireEvent.click(screen.getByRole("button", { name: /cancelar/i }));

    await waitFor(() => {
      expect(screen.queryByText("Remover fatura")).not.toBeInTheDocument();
    });
  });

  it("shows empty state when no invoices found", async () => {
    server.use(
      http.get("/api/proxy/admin/billing/invoices/", () =>
        HttpResponse.json({
          success: true,
          data: { count: 0, num_pages: 1, page: 1, results: [] },
          error: null,
        })
      )
    );

    renderWithProviders(<BackofficeInvoicesPage />);

    await waitFor(() => {
      expect(screen.getByText(/nenhuma fatura encontrada/i)).toBeInTheDocument();
    });
  });

  it("does not show pagination when there is only 1 page", async () => {
    renderWithProviders(<BackofficeInvoicesPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    expect(screen.queryByRole("button", { name: /anterior/i })).not.toBeInTheDocument();
  });

  it("shows billing_type column header", async () => {
    renderWithProviders(<BackofficeInvoicesPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    expect(screen.getByText(/pagamento/i)).toBeInTheDocument();
  });

  it("shows billing_type labels for each invoice row", async () => {
    renderWithProviders(<BackofficeInvoicesPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    expect(screen.getByText("Boleto bancário")).toBeInTheDocument();
    expect(screen.getByText("Pix")).toBeInTheDocument();
  });

  it("opens create modal with billing_type selector", async () => {
    renderWithProviders(<BackofficeInvoicesPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    fireEvent.click(screen.getByRole("button", { name: /nova fatura/i }));

    await waitFor(() => {
      expect(screen.getByText(/nova fatura avulsa/i)).toBeInTheDocument();
      expect(screen.getByText(/forma de pagamento/i)).toBeInTheDocument();
    });
  });

  it("billing_type selector defaults to BOLETO", async () => {
    renderWithProviders(<BackofficeInvoicesPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    fireEvent.click(screen.getByRole("button", { name: /nova fatura/i }));

    await waitFor(() => screen.getByText(/nova fatura avulsa/i));

    const selects = screen.getAllByRole("combobox");
    const billingSelect = selects.find((s) =>
      Array.from(s.querySelectorAll("option")).some((o) => o.textContent === "Boleto bancário")
    );
    expect(billingSelect).toBeDefined();
    expect((billingSelect as HTMLSelectElement).value).toBe("BOLETO");
  });
});
