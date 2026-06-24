import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, fireEvent, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import BackofficeCustomersPage from "@/app/backoffice/customers/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/backoffice/customers",
  useSearchParams: () => ({ get: () => null }),
}));

describe("BackofficeCustomersPage", () => {
  it("renders customer list after loading", async () => {
    renderWithProviders(<BackofficeCustomersPage />);

    await waitFor(() => {
      expect(screen.getByText("Acme Ltda")).toBeInTheDocument();
      expect(screen.getByText("Mega Corp")).toBeInTheDocument();
    });

    expect(screen.getByText("00.000.000/0001-00")).toBeInTheDocument();
    expect(screen.getByText("11.111.111/0001-11")).toBeInTheDocument();
  });

  it("shows correct status badges", async () => {
    renderWithProviders(<BackofficeCustomersPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    // Status text also appears in filter <option>s — use getAllByText
    expect(screen.getAllByText("Ativo").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Suspenso").length).toBeGreaterThanOrEqual(1);
  });

  it("shows suspend button for active customers", async () => {
    renderWithProviders(<BackofficeCustomersPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    const suspendBtns = screen.getAllByRole("button", { name: /suspender/i });
    expect(suspendBtns.length).toBeGreaterThanOrEqual(1);
  });

  it("shows reactivate button for suspended customers", async () => {
    renderWithProviders(<BackofficeCustomersPage />);

    await waitFor(() => screen.getByText("Mega Corp"));

    const reactivateBtns = screen.getAllByRole("button", { name: /reativar/i });
    expect(reactivateBtns.length).toBeGreaterThanOrEqual(1);
  });

  it("opens confirmation dialog when clicking suspend", async () => {
    renderWithProviders(<BackofficeCustomersPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    const [suspendBtn] = screen.getAllByRole("button", { name: /suspender/i });
    fireEvent.click(suspendBtn);

    await waitFor(() => {
      expect(screen.getByText("Suspender cliente")).toBeInTheDocument();
      expect(screen.getByText(/api keys e acessos aos serviços ativos serão suspensos/i)).toBeInTheDocument();
    });
  });

  it("closes dialog on cancel", async () => {
    renderWithProviders(<BackofficeCustomersPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    const [suspendBtn] = screen.getAllByRole("button", { name: /suspender/i });
    fireEvent.click(suspendBtn);
    await waitFor(() => screen.getByText("Suspender cliente"));

    const cancelBtn = screen.getByRole("button", { name: /voltar/i });
    fireEvent.click(cancelBtn);

    await waitFor(() => {
      expect(screen.queryByText("Suspender cliente")).not.toBeInTheDocument();
    });
  });

  it("does not show bulk action bar when nothing is selected", async () => {
    renderWithProviders(<BackofficeCustomersPage />);
    await waitFor(() => screen.getByText("Acme Ltda"));
    expect(screen.queryByText(/selecionado/i)).not.toBeInTheDocument();
  });

  it("shows bulk action bar after selecting a row", async () => {
    renderWithProviders(<BackofficeCustomersPage />);
    await waitFor(() => screen.getByText("Acme Ltda"));

    const checkboxes = screen.getAllByRole("checkbox");
    // checkboxes[0] = select-all header; checkboxes[1] = first row (Acme Ltda)
    fireEvent.click(checkboxes[1]);

    await waitFor(() => {
      expect(screen.getByText(/1 selecionado/i)).toBeInTheDocument();
    });
  });

  it("select-all checkbox selects all rows", async () => {
    renderWithProviders(<BackofficeCustomersPage />);
    await waitFor(() => screen.getByText("Acme Ltda"));

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]); // select-all

    await waitFor(() => {
      expect(screen.getByText(/2 selecionados/i)).toBeInTheDocument();
    });
  });

  it("clearing selection hides bulk action bar", async () => {
    renderWithProviders(<BackofficeCustomersPage />);
    await waitFor(() => screen.getByText("Acme Ltda"));

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[1]);
    await waitFor(() => screen.getByText(/1 selecionado/i));

    fireEvent.click(screen.getByText(/limpar seleção/i));
    await waitFor(() => {
      expect(screen.queryByText(/selecionado/i)).not.toBeInTheDocument();
    });
  });

  it("bulk suspend calls suspend API for active customers", async () => {
    let suspendCalled = false;
    server.use(
      http.post("/api/proxy/admin/customers/c1/suspend/", () => {
        suspendCalled = true;
        return HttpResponse.json({
          success: true,
          data: { id: "c1", company_name: "Acme Ltda", document: "00.000.000/0001-00", status: "suspended", asaas_customer_id: "", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-06-10T00:00:00Z" },
          error: null,
        });
      })
    );

    renderWithProviders(<BackofficeCustomersPage />);
    await waitFor(() => screen.getByText("Acme Ltda"));

    // Select first row (Acme Ltda — active)
    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[1]);
    await waitFor(() => screen.getByText(/1 selecionado/i));

    // Click bulk Suspender button in the action bar
    const bulkBar = screen.getByText(/1 selecionado/i).closest("div")!;
    const suspendBtn = within(bulkBar).getByRole("button", { name: /suspender/i });
    fireEvent.click(suspendBtn);

    await waitFor(() => {
      expect(suspendCalled).toBe(true);
    });
  });

  it("bulk cancel shows inline confirmation before calling API", async () => {
    let cancelCalled = false;
    server.use(
      http.post("/api/proxy/admin/customers/:id/cancel/", ({ params }) => {
        cancelCalled = true;
        return HttpResponse.json({
          success: true,
          data: { id: params.id, company_name: "Acme Ltda", document: "00.000.000/0001-00", status: "cancelled", asaas_customer_id: "", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-06-10T00:00:00Z" },
          error: null,
        });
      })
    );

    renderWithProviders(<BackofficeCustomersPage />);
    await waitFor(() => screen.getByText("Acme Ltda"));

    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[1]);
    await waitFor(() => screen.getByText(/1 selecionado/i));

    // First click shows inline confirmation — scope to the bulk action bar
    const bulkBar = screen.getByText(/1 selecionado/i).closest("div")!;
    const cancelBtn = within(bulkBar).getByRole("button", { name: /^cancelar$/i });
    fireEvent.click(cancelBtn);

    await waitFor(() => {
      expect(screen.getByText(/cancelar.*cliente/i)).toBeInTheDocument();
    });
    expect(cancelCalled).toBe(false); // not yet called

    // Click "Confirmar" triggers the actual API call
    fireEvent.click(screen.getByRole("button", { name: /confirmar/i }));
    await waitFor(() => {
      expect(cancelCalled).toBe(true);
    });
  });

  it("CSV export button does not throw when customers selected", async () => {
    renderWithProviders(<BackofficeCustomersPage />);
    await waitFor(() => screen.getByText("Acme Ltda"));

    // Select all
    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);
    await waitFor(() => screen.getByText(/2 selecionados/i));

    // jsdom doesn't support URL.createObjectURL — stub it
    const createObjectURL = vi.fn(() => "blob:fake");
    const revokeObjectURL = vi.fn();
    Object.assign(window.URL, { createObjectURL, revokeObjectURL });

    const exportBtn = screen.getByRole("button", { name: /exportar csv/i });
    expect(() => fireEvent.click(exportBtn)).not.toThrow();
    expect(createObjectURL).toHaveBeenCalled();
  });

  it("shows empty state when no customers found", async () => {
    server.use(
      http.get("/api/proxy/admin/customers/", () =>
        HttpResponse.json({
          success: true,
          data: { count: 0, next: null, previous: null, results: [] },
          error: null,
        })
      )
    );

    renderWithProviders(<BackofficeCustomersPage />);

    await waitFor(() => {
      expect(screen.getByText(/nenhum cliente encontrado/i)).toBeInTheDocument();
    });
  });

  it("opens create customer modal with CNPJ field", async () => {
    renderWithProviders(<BackofficeCustomersPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    fireEvent.click(screen.getByRole("button", { name: /novo cliente/i }));

    // Use placeholder as the discriminator — it only exists inside the modal
    await waitFor(() => {
      expect(screen.getByPlaceholderText("00.000.000/0000-00")).toBeInTheDocument();
    });
  });

  it("applies CNPJ mask as user types digits", async () => {
    renderWithProviders(<BackofficeCustomersPage />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    fireEvent.click(screen.getByRole("button", { name: /novo cliente/i }));

    await waitFor(() => screen.getByPlaceholderText("00.000.000/0000-00"));

    const cnpjInput = screen.getByPlaceholderText("00.000.000/0000-00");
    fireEvent.change(cnpjInput, { target: { value: "11222333000181" } });

    await waitFor(() => {
      expect((cnpjInput as HTMLInputElement).value).toBe("11.222.333/0001-81");
    });
  });
});
