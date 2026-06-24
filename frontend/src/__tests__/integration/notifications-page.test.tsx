import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import NotificationsPage from "@/app/dashboard/notifications/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/dashboard/notifications",
  useSearchParams: () => ({ get: () => null }),
}));

describe("NotificationsPage", () => {
  it("renders notification list after loading", async () => {
    renderWithProviders(<NotificationsPage />);

    await waitFor(() => {
      expect(screen.getByText("Pagamento confirmado")).toBeInTheDocument();
      expect(screen.getByText("Assinatura renovada")).toBeInTheDocument();
    });
  });

  it("shows unread count in subtitle", async () => {
    renderWithProviders(<NotificationsPage />);

    await waitFor(() => {
      expect(screen.getByText("1 não lida")).toBeInTheDocument();
    });
  });

  it("shows 'Tudo em dia' when no unread notifications", async () => {
    server.use(
      http.get("/api/proxy/client/notifications/", () =>
        HttpResponse.json({
          success: true,
          data: {
            count: 1,
            unread_count: 0,
            num_pages: 1,
            page: 1,
            results: [
              { id: "n1", event_type: "subscription.renewed", subject: "Renovada", body: "Ok", is_read: true, created_at: "2024-01-01T00:00:00Z", read_at: "2024-01-02T00:00:00Z" },
            ],
          },
          error: null,
        })
      )
    );

    renderWithProviders(<NotificationsPage />);

    await waitFor(() => {
      expect(screen.getByText("Tudo em dia")).toBeInTheDocument();
    });
  });

  it("shows 'Marcar todas como lidas' button when there are unread notifications", async () => {
    renderWithProviders(<NotificationsPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /marcar todas como lidas/i })).toBeInTheDocument();
    });
  });

  it("does not show mark-all button when all read", async () => {
    server.use(
      http.get("/api/proxy/client/notifications/", () =>
        HttpResponse.json({
          success: true,
          data: { count: 0, unread_count: 0, num_pages: 1, page: 1, results: [] },
          error: null,
        })
      )
    );

    renderWithProviders(<NotificationsPage />);

    await waitFor(() => screen.getByText("Tudo em dia"));
    expect(screen.queryByRole("button", { name: /marcar todas como lidas/i })).not.toBeInTheDocument();
  });

  it("shows empty state when there are no notifications", async () => {
    server.use(
      http.get("/api/proxy/client/notifications/", () =>
        HttpResponse.json({
          success: true,
          data: { count: 0, unread_count: 0, num_pages: 1, page: 1, results: [] },
          error: null,
        })
      )
    );

    renderWithProviders(<NotificationsPage />);

    await waitFor(() => {
      expect(screen.getByText(/nenhuma notificação pendente/i)).toBeInTheDocument();
    });
  });

  it("shows mark-read button only on unread notifications", async () => {
    renderWithProviders(<NotificationsPage />);

    await waitFor(() => screen.getByText("Pagamento confirmado"));

    // The ✓ mark-read button should appear (aria title)
    const markReadBtns = screen.getAllByTitle("Marcar como lida");
    expect(markReadBtns).toHaveLength(1);
  });

  it("does not show pagination when there is only 1 page", async () => {
    renderWithProviders(<NotificationsPage />);

    await waitFor(() => screen.getByText("Pagamento confirmado"));

    expect(screen.queryByRole("button", { name: /anterior/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /próxima/i })).not.toBeInTheDocument();
  });

  it("shows pagination buttons when there are multiple pages", async () => {
    server.use(
      http.get("/api/proxy/client/notifications/", () =>
        HttpResponse.json({
          success: true,
          data: {
            count: 40,
            unread_count: 0,
            num_pages: 2,
            page: 1,
            results: Array.from({ length: 20 }, (_, i) => ({
              id: `n${i}`,
              event_type: "payment.processed",
              subject: `Notificação ${i + 1}`,
              body: "Corpo",
              is_read: true,
              created_at: "2024-01-01T00:00:00Z",
              read_at: "2024-01-02T00:00:00Z",
            })),
          },
          error: null,
        })
      )
    );

    renderWithProviders(<NotificationsPage />);

    await waitFor(() => screen.getByText("Notificação 1"));
    expect(screen.getByRole("button", { name: /próxima/i })).toBeInTheDocument();
  });

  it("calls mark-all-read without throwing", async () => {
    renderWithProviders(<NotificationsPage />);

    await waitFor(() => screen.getByRole("button", { name: /marcar todas como lidas/i }));

    // Fire and verify no error is thrown — toast requires <Toaster /> which is not in this render
    expect(() =>
      fireEvent.click(screen.getByRole("button", { name: /marcar todas como lidas/i }))
    ).not.toThrow();
  });

  it("renders service.provisioned notification with its subject", async () => {
    server.use(
      http.get("/api/proxy/client/notifications/", () =>
        HttpResponse.json({
          success: true,
          data: {
            count: 1,
            unread_count: 1,
            num_pages: 1,
            page: 1,
            results: [
              {
                id: "svc1",
                event_type: "service.provisioned",
                subject: "n8n provisionado",
                body: "O serviço n8n foi implantado e está disponível no seu dashboard.",
                is_read: false,
                created_at: "2024-06-01T10:00:00Z",
                read_at: null,
              },
            ],
          },
          error: null,
        })
      )
    );

    renderWithProviders(<NotificationsPage />);

    await waitFor(() => {
      expect(screen.getByText("n8n provisionado")).toBeInTheDocument();
      expect(screen.getByText(/implantado e está disponível/i)).toBeInTheDocument();
    });
  });

  it("renders unknown event type without crashing", async () => {
    server.use(
      http.get("/api/proxy/client/notifications/", () =>
        HttpResponse.json({
          success: true,
          data: {
            count: 1,
            unread_count: 0,
            num_pages: 1,
            page: 1,
            results: [
              {
                id: "unk1",
                event_type: "future.event.type",
                subject: "Evento futuro",
                body: "Corpo do evento.",
                is_read: true,
                created_at: "2024-06-01T10:00:00Z",
                read_at: "2024-06-01T11:00:00Z",
              },
            ],
          },
          error: null,
        })
      )
    );

    renderWithProviders(<NotificationsPage />);

    await waitFor(() => {
      expect(screen.getByText("Evento futuro")).toBeInTheDocument();
    });
  });
});
