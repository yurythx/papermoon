import { screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import SubscriptionsPage from "@/app/dashboard/subscriptions/page";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/dashboard/subscriptions",
  useParams: () => ({}),
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("SubscriptionsPage", () => {
  it("renders subscription list", async () => {
    renderWithProviders(<SubscriptionsPage />);
    await waitFor(() =>
      expect(screen.getByText("Atendimento WhatsApp")).toBeTruthy()
    );
  });

  it("shows billing cycle", async () => {
    renderWithProviders(<SubscriptionsPage />);
    await waitFor(() => expect(screen.getByText("Mensal")).toBeTruthy());
  });

  it("shows subscription amount", async () => {
    renderWithProviders(<SubscriptionsPage />);
    // parseFloat("199.00").toFixed(2) → "199.00" (period, no locale comma)
    await waitFor(() => expect(screen.getByText(/199\.00/)).toBeTruthy());
  });

  it("shows active status badge", async () => {
    renderWithProviders(<SubscriptionsPage />);
    await waitFor(() => expect(screen.getByText("Ativo")).toBeTruthy());
  });

  it("shows contact link for changes", async () => {
    renderWithProviders(<SubscriptionsPage />);
    await waitFor(() =>
      expect(screen.getByText(/Fale com nossa equipe/i)).toBeTruthy()
    );
  });

  it("shows empty state when no subscriptions", async () => {
    const { http, HttpResponse } = await import("msw");
    const { server } = await import("../mocks/server");
    server.use(
      http.get("/api/proxy/client/subscriptions/", () =>
        HttpResponse.json({ success: true, data: { count: 0, next: null, previous: null, results: [] }, error: null })
      )
    );
    renderWithProviders(<SubscriptionsPage />);
    await waitFor(() =>
      expect(screen.getByText(/nenhum serviço/i)).toBeTruthy()
    );
  });

  it("shows service accesses when license exists", async () => {
    renderWithProviders(<SubscriptionsPage />);
    await waitFor(() =>
      expect(screen.getByText("Serviços incluídos")).toBeTruthy()
    );
  });
});
