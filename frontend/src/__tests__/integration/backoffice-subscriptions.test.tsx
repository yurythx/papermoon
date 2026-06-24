import { screen, waitFor, fireEvent, act } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import BackofficeSubscriptionsPage from "@/app/backoffice/subscriptions/page";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/backoffice/subscriptions",
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("BackofficeSubscriptionsPage", () => {
  it("renders subscriptions list", async () => {
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() =>
      expect(screen.getAllByText("Atendimento WhatsApp").length).toBeGreaterThan(0)
    );
  });

  it("shows active subscription status badge", async () => {
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() => expect(screen.getByText("Ativa")).toBeTruthy());
  });

  it("shows suspended subscription status badge", async () => {
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() => expect(screen.getByText("Suspensa")).toBeTruthy());
  });

  it("shows Suspender button for active subscription", async () => {
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Suspender" })).toBeTruthy()
    );
  });

  it("shows Cancelar button for active subscription", async () => {
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() =>
      expect(screen.getAllByRole("button", { name: "Cancelar" }).length).toBeGreaterThan(0)
    );
  });

  it("opens confirm dialog on action click", async () => {
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() => screen.getByRole("button", { name: "Suspender" }));
    fireEvent.click(screen.getByRole("button", { name: "Suspender" }));
    // Dialog title comes from ACTION_META.suspend.title
    expect(screen.getByText("Suspender assinatura")).toBeTruthy();
  });

  it("closes confirm dialog on cancel click", async () => {
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() => screen.getByRole("button", { name: "Suspender" }));
    fireEvent.click(screen.getByRole("button", { name: "Suspender" }));
    fireEvent.click(screen.getByRole("button", { name: "Voltar" }));
    await waitFor(() =>
      expect(screen.queryByText("Suspender assinatura")).toBeNull()
    );
  });

  it("shows empty state when no subscriptions", async () => {
    const { http, HttpResponse } = await import("msw");
    const { server } = await import("../mocks/server");
    server.use(
      http.get("/api/proxy/admin/subscriptions/", () =>
        HttpResponse.json({ success: true, data: { count: 0, next: null, previous: null, results: [] }, error: null })
      )
    );
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() =>
      expect(screen.getByText(/Nenhuma assinatura encontrada/)).toBeTruthy()
    );
  });

  it("shows Nova assinatura button", async () => {
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /nova assinatura/i })).toBeInTheDocument()
    );
  });

  it("opens create subscription modal", async () => {
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() => screen.getByRole("button", { name: /nova assinatura/i }));
    fireEvent.click(screen.getByRole("button", { name: /nova assinatura/i }));
    await waitFor(() =>
      expect(screen.getByText(/assinatura será criada manualmente/i)).toBeInTheDocument()
    );
  });

  it("modal shows customer and product selects", async () => {
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() => screen.getByRole("button", { name: /nova assinatura/i }));
    fireEvent.click(screen.getByRole("button", { name: /nova assinatura/i }));
    await waitFor(() => screen.getByText(/assinatura será criada manualmente/i));
    const selects = screen.getAllByRole("combobox");
    expect(selects.length).toBeGreaterThanOrEqual(2);
  });

  it("modal closes on cancel", async () => {
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() => screen.getByRole("button", { name: /nova assinatura/i }));
    fireEvent.click(screen.getByRole("button", { name: /nova assinatura/i }));
    await waitFor(() => screen.getByText(/assinatura será criada manualmente/i));
    fireEvent.click(screen.getByRole("button", { name: /^fechar$/i }));
    await waitFor(() =>
      expect(screen.queryByText(/assinatura será criada manualmente/i)).toBeNull()
    );
  });

  it("shows Detalhe link for each subscription", async () => {
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() =>
      expect(screen.getAllByRole("link", { name: "Detalhe" }).length).toBeGreaterThanOrEqual(2)
    );
  });

  it("shows search input", async () => {
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/buscar por cliente/i)).toBeInTheDocument()
    );
  });

  it("search filters subscriptions by customer name", async () => {
    renderWithProviders(<BackofficeSubscriptionsPage />);
    await waitFor(() => screen.getAllByText("Atendimento WhatsApp").length >= 2);

    const input = screen.getByPlaceholderText(/buscar por cliente/i);
    await act(async () => { fireEvent.change(input, { target: { value: "Acme" } }); });

    // After debounce + mock filtering, only Acme's sub should remain
    await waitFor(() => {
      expect(screen.getByText("Acme Ltda")).toBeInTheDocument();
      expect(screen.queryByText("Beta Corp")).toBeNull();
    }, { timeout: 1500 });
  });
});
