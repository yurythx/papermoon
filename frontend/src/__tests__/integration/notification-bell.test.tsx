import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import NotificationBell from "@/components/NotificationBell";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/dashboard",
  useSearchParams: () => ({ get: () => null }),
}));

// Provide a logged-in user with a customer so the notification query is enabled
vi.mock("@/store/auth", () => ({
  useAuthStore: () => ({
    me: {
      user: { id: "u1", email: "test@example.com", username: "test", is_staff: false },
      customer: { id: "c1", company_name: "Test Co", status: "active" },
      role: "owner",
    },
  }),
}));

describe("NotificationBell", () => {
  it("renders bell icon", () => {
    renderWithProviders(<NotificationBell />);
    expect(screen.getByRole("button", { name: /notificações/i })).toBeInTheDocument();
  });

  it("shows unread badge when there are unread notifications", async () => {
    renderWithProviders(<NotificationBell />);
    await waitFor(() => {
      expect(screen.getByText("1")).toBeInTheDocument();
    });
  });

  it("hides badge when there are no unread notifications", async () => {
    server.use(
      http.get("/api/proxy/client/notifications/", () =>
        HttpResponse.json({
          success: true,
          data: { count: 0, unread_count: 0, results: [] },
          error: null,
        })
      )
    );
    renderWithProviders(<NotificationBell />);
    await waitFor(() => {
      expect(screen.queryByText("1")).not.toBeInTheDocument();
    });
  });

  it("opens dropdown on click and shows notifications", async () => {
    renderWithProviders(<NotificationBell />);
    await waitFor(() => screen.getByText("1")); // badge loaded

    fireEvent.click(screen.getByRole("button", { name: /notificações/i }));

    await waitFor(() => {
      expect(screen.getByText("Notificações")).toBeInTheDocument();
      expect(screen.getByText("Pagamento confirmado")).toBeInTheDocument();
      expect(screen.getByText("Assinatura renovada")).toBeInTheDocument();
    });
  });

  it("shows mark all as read button only when there are unread notifications", async () => {
    renderWithProviders(<NotificationBell />);
    await waitFor(() => screen.getByText("1"));

    fireEvent.click(screen.getByRole("button", { name: /notificações/i }));

    await waitFor(() => {
      expect(screen.getByText("Marcar todas como lidas")).toBeInTheDocument();
    });
  });

  it("does not show mark all read when all are read", async () => {
    server.use(
      http.get("/api/proxy/client/notifications/", () =>
        HttpResponse.json({
          success: true,
          data: {
            count: 1,
            unread_count: 0,
            results: [
              { id: "n1", event_type: "subscription.renewed", subject: "Renovada", body: "Ok", is_read: true, created_at: "2024-01-01T00:00:00Z", read_at: "2024-01-02T00:00:00Z" },
            ],
          },
          error: null,
        })
      )
    );

    renderWithProviders(<NotificationBell />);
    fireEvent.click(screen.getByRole("button", { name: /notificações/i }));

    await waitFor(() => screen.getByText("Renovada"));
    expect(screen.queryByText("Marcar todas como lidas")).not.toBeInTheDocument();
  });

  it("shows empty state when there are no notifications", async () => {
    server.use(
      http.get("/api/proxy/client/notifications/", () =>
        HttpResponse.json({
          success: true,
          data: { count: 0, unread_count: 0, results: [] },
          error: null,
        })
      )
    );

    renderWithProviders(<NotificationBell />);
    fireEvent.click(screen.getByRole("button", { name: /notificações/i }));

    await waitFor(() => {
      expect(screen.getByText(/nenhuma notificação/i)).toBeInTheDocument();
    });
  });

  it("renders service.provisioned notification in dropdown", async () => {
    server.use(
      http.get("/api/proxy/client/notifications/", () =>
        HttpResponse.json({
          success: true,
          data: {
            count: 1,
            unread_count: 1,
            results: [
              {
                id: "svc1",
                event_type: "service.provisioned",
                subject: "Chatwoot provisionado",
                body: "O serviço Chatwoot foi implantado.",
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

    renderWithProviders(<NotificationBell />);
    await waitFor(() => screen.getByText("1"));

    fireEvent.click(screen.getByRole("button", { name: /notificações/i }));

    await waitFor(() => {
      expect(screen.getByText("Chatwoot provisionado")).toBeInTheDocument();
    });
  });
});
