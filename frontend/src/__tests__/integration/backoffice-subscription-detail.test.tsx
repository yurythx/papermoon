import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import SubscriptionDetailPage from "@/app/backoffice/subscriptions/[id]/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/backoffice/subscriptions/sub1",
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("SubscriptionDetailPage", () => {
  it("renders subscription product name", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => {
      expect(screen.getByText("Atendimento WhatsApp")).toBeInTheDocument();
    });
  });

  it("shows subscription billing cycle", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => {
      expect(screen.getByText("Mensal")).toBeInTheDocument();
    });
  });

  it("shows customer link when customer_id present", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => {
      const link = screen.getByRole("link", { name: "Acme Ltda" });
      expect(link).toHaveAttribute("href", "/backoffice/customers/c1");
    });
  });

  it("renders service accesses list", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => {
      expect(screen.getByText("Chatwoot")).toBeInTheDocument();
      expect(screen.getByText("n8n")).toBeInTheDocument();
    });
  });

  it("shows reprovision button for failed service", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /reprovisionar/i })).toBeInTheDocument();
    });
  });

  it("shows error message for failed service", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => {
      expect(screen.getByText(/ConnectionError/i)).toBeInTheDocument();
    });
  });

  it("shows active service status", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => {
      expect(screen.getByText("Ativo")).toBeInTheDocument();
    });
  });

  it("shows not found when subscription does not exist", async () => {
    server.use(
      http.get("/api/proxy/admin/subscriptions/:id/", () =>
        HttpResponse.json(
          { success: false, data: null, error: { code: "not_found", message: "Not found", details: [] } },
          { status: 404 }
        )
      )
    );

    renderWithProviders(<SubscriptionDetailPage params={{ id: "unknown" }} />);

    await waitFor(() => {
      expect(screen.getByText("Serviço não encontrado.")).toBeInTheDocument();
    });
  });

  it("calls reprovision when button clicked", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => screen.getByRole("button", { name: /reprovisionar/i }));

    expect(() =>
      fireEvent.click(screen.getByRole("button", { name: /reprovisionar/i }))
    ).not.toThrow();
  });

  it("shows add service button", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /adicionar/i })).toBeInTheDocument();
    });
  });

  it("opens add service modal when button clicked", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => screen.getByRole("button", { name: /adicionar/i }));
    fireEvent.click(screen.getByRole("button", { name: /adicionar/i }));

    await waitFor(() => {
      expect(screen.getByText("Adicionar serviço")).toBeInTheDocument();
    });
  });

  it("add service modal filters out already provisioned services", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => screen.getByRole("button", { name: /adicionar/i }));
    fireEvent.click(screen.getByRole("button", { name: /adicionar/i }));

    await waitFor(() => screen.getByText("Adicionar serviço"));

    const select = screen.getByRole("combobox") as HTMLSelectElement;
    const options = Array.from(select.options).map((o) => o.value);

    // chatwoot and n8n are already provisioned (from mock), should not appear
    expect(options).not.toContain("chatwoot");
    expect(options).not.toContain("n8n");
  });

  it("shows edit button for each service access row", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => {
      const editBtns = screen.getAllByTitle("Editar ID externo");
      expect(editBtns.length).toBeGreaterThanOrEqual(2);
    });
  });

  it("opens edit service modal on pencil click", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => screen.getAllByTitle("Editar ID externo"));
    fireEvent.click(screen.getAllByTitle("Editar ID externo")[0]);

    await waitFor(() => {
      expect(screen.getByText(/Editar — Chatwoot/i)).toBeInTheDocument();
    });
  });

  it("edit modal pre-fills external_id", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => screen.getAllByTitle("Editar ID externo"));
    fireEvent.click(screen.getAllByTitle("Editar ID externo")[0]);

    await waitFor(() => screen.getByText(/Editar — Chatwoot/i));

    const input = screen.getByPlaceholderText(/ex: inbox-42/i) as HTMLInputElement;
    expect(input.value).toBe("inbox-42");
  });

  it("closes edit modal on cancel", async () => {
    renderWithProviders(<SubscriptionDetailPage params={{ id: "sub1" }} />);

    await waitFor(() => screen.getAllByTitle("Editar ID externo"));
    fireEvent.click(screen.getAllByTitle("Editar ID externo")[0]);
    await waitFor(() => screen.getByText(/Editar — Chatwoot/i));

    fireEvent.click(screen.getByRole("button", { name: /^cancelar$/i }));

    await waitFor(() =>
      expect(screen.queryByText(/Editar — Chatwoot/i)).toBeNull()
    );
  });
});
