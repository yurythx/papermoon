import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import CustomerDetailPage from "@/app/backoffice/customers/[id]/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/backoffice/customers/c1",
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("CustomerDetailPage", () => {
  it("renders customer name and document after loading", async () => {
    renderWithProviders(<CustomerDetailPage params={{ id: "c1" }} />);

    await waitFor(() => {
      expect(screen.getByText("Acme Ltda")).toBeInTheDocument();
      expect(screen.getByText("00.000.000/0001-00")).toBeInTheDocument();
    });
  });

  it("renders the breadcrumb back link", async () => {
    renderWithProviders(<CustomerDetailPage params={{ id: "c1" }} />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    const link = screen.getByRole("link", { name: /clientes/i });
    expect(link).toHaveAttribute("href", "/backoffice/customers");
  });

  it("shows suspend button for active customer", async () => {
    renderWithProviders(<CustomerDetailPage params={{ id: "c1" }} />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    expect(screen.getByRole("button", { name: /suspender/i })).toBeInTheDocument();
  });

  it("shows reactivate button for suspended customer", async () => {
    renderWithProviders(<CustomerDetailPage params={{ id: "c2" }} />);

    await waitFor(() => screen.getByText("Mega Corp"));

    expect(screen.getByRole("button", { name: /reativar/i })).toBeInTheDocument();
  });

  it("shows cancel button for non-cancelled customers", async () => {
    renderWithProviders(<CustomerDetailPage params={{ id: "c1" }} />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    expect(screen.getByRole("button", { name: /cancelar conta/i })).toBeInTheDocument();
  });

  it("opens confirmation dialog when clicking suspend", async () => {
    renderWithProviders(<CustomerDetailPage params={{ id: "c1" }} />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    fireEvent.click(screen.getByRole("button", { name: /suspender/i }));

    await waitFor(() => {
      expect(screen.getByText("Suspender cliente")).toBeInTheDocument();
      expect(screen.getByText(/api keys e acessos aos serviços ativos serão suspensos/i)).toBeInTheDocument();
    });
  });

  it("closes dialog when clicking Voltar", async () => {
    renderWithProviders(<CustomerDetailPage params={{ id: "c1" }} />);

    await waitFor(() => screen.getByText("Acme Ltda"));

    fireEvent.click(screen.getByRole("button", { name: /suspender/i }));
    await waitFor(() => screen.getByText("Suspender cliente"));

    fireEvent.click(screen.getByRole("button", { name: /voltar/i }));

    await waitFor(() => {
      expect(screen.queryByText("Suspender cliente")).not.toBeInTheDocument();
    });
  });

  it("renders subscriptions section", async () => {
    renderWithProviders(<CustomerDetailPage params={{ id: "c1" }} />);

    await waitFor(() => screen.getByText("Acme Ltda"));
    await waitFor(() => {
      expect(screen.getByText(/assinaturas/i)).toBeInTheDocument();
    });
  });

  it("renders invoices section", async () => {
    renderWithProviders(<CustomerDetailPage params={{ id: "c1" }} />);

    await waitFor(() => screen.getByText("Acme Ltda"));
    await waitFor(() => {
      expect(screen.getByText(/faturas recentes/i)).toBeInTheDocument();
    });
  });

  it("shows not found state for unknown customer", async () => {
    server.use(
      http.get("/api/proxy/admin/customers/:id/", () =>
        HttpResponse.json(
          { success: false, data: null, error: { code: "not_found", message: "Not found", details: [] } },
          { status: 404 }
        )
      )
    );

    renderWithProviders(<CustomerDetailPage params={{ id: "unknown" }} />);

    await waitFor(() => {
      expect(screen.getByText("Cliente não encontrado.")).toBeInTheDocument();
    });
  });

  it("shows Asaas ID when present", async () => {
    renderWithProviders(<CustomerDetailPage params={{ id: "c1" }} />);

    await waitFor(() => screen.getByText("Acme Ltda"));
    await waitFor(() => {
      expect(screen.getByText("asaas-c1")).toBeInTheDocument();
    });
  });

  it("shows quota section with usage stats", async () => {
    renderWithProviders(<CustomerDetailPage params={{ id: "c1" }} />);

    await waitFor(() => screen.getByText("Acme Ltda"));
    await waitFor(() => {
      expect(screen.getByText("Quota de API")).toBeInTheDocument();
      expect(screen.getByText(/3\.200/)).toBeInTheDocument();
    });
  });
});
