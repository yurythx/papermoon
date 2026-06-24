import { screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import BackofficeProductsPage from "@/app/backoffice/products/page";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/backoffice/products",
}));

describe("BackofficeProductsPage", () => {
  it("renders product names", async () => {
    renderWithProviders(<BackofficeProductsPage />);
    await waitFor(() => expect(screen.getByText("Atendimento WhatsApp")).toBeTruthy());
  });

  it("shows both active and inactive products", async () => {
    renderWithProviders(<BackofficeProductsPage />);
    await waitFor(() => {
      expect(screen.getByText("Atendimento WhatsApp")).toBeTruthy();
      expect(screen.getByText("GLPI Helpdesk")).toBeTruthy();
    });
  });

  it("shows active badge for active product", async () => {
    renderWithProviders(<BackofficeProductsPage />);
    await waitFor(() => expect(screen.getByText("Ativo")).toBeTruthy());
  });

  it("shows inactive badge for inactive product", async () => {
    renderWithProviders(<BackofficeProductsPage />);
    await waitFor(() => expect(screen.getByText("Inativo")).toBeTruthy());
  });

  it("shows service component key", async () => {
    renderWithProviders(<BackofficeProductsPage />);
    await waitFor(() => expect(screen.getByText("n8n")).toBeTruthy());
  });

  it("toggle button click does not throw", async () => {
    renderWithProviders(<BackofficeProductsPage />);
    await waitFor(() => screen.getByText("Atendimento WhatsApp"));
    const buttons = screen.getAllByRole("button");
    expect(() => fireEvent.click(buttons[0])).not.toThrow();
  });

  it("shows empty state when no products", async () => {
    const { http, HttpResponse } = await import("msw");
    const { server } = await import("../mocks/server");
    server.use(
      http.get("/api/proxy/admin/products/", () =>
        HttpResponse.json({ success: true, data: [], error: null })
      )
    );
    renderWithProviders(<BackofficeProductsPage />);
    await waitFor(() =>
      expect(screen.getByText(/Nenhum produto cadastrado/)).toBeTruthy()
    );
  });
});
