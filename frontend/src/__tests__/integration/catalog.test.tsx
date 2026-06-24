import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import CatalogPage from "@/app/dashboard/catalog/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
  usePathname: () => "/dashboard/catalog",
  useSearchParams: () => ({ get: () => null }),
}));

describe("CatalogPage", () => {
  beforeEach(() => pushMock.mockClear());
  it("renders products from catalog", async () => {
    renderWithProviders(<CatalogPage />);

    await waitFor(() => {
      expect(screen.getByText("Atendimento WhatsApp")).toBeInTheDocument();
    });

    expect(screen.getByText("Ideal para pequenas equipes")).toBeInTheDocument();
    expect(screen.getByText("n8n")).toBeInTheDocument();
  });

  it("renders pricing labels for each billing cycle", async () => {
    renderWithProviders(<CatalogPage />);
    await waitFor(() => screen.getByText("Atendimento WhatsApp"));

    // Page shows "Mensal" and "Anual" as text labels (read-only, not buttons)
    expect(screen.getAllByText(/mensal/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/anual/i).length).toBeGreaterThan(0);
  });

  it("shows contact CTA banner", async () => {
    renderWithProviders(<CatalogPage />);
    await waitFor(() => screen.getByText("Atendimento WhatsApp"));
    expect(screen.getByText(/quer contratar um novo serviço/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /falar com a equipe/i })).toBeInTheDocument();
  });

  it("shows price amounts for products", async () => {
    renderWithProviders(<CatalogPage />);
    await waitFor(() => screen.getByText("Atendimento WhatsApp"));
    // Mock data includes amounts — at least one price is shown
    expect(screen.getAllByText(/R\$/).length).toBeGreaterThan(0);
  });

  it("shows service component badges on product cards", async () => {
    renderWithProviders(<CatalogPage />);
    await waitFor(() => screen.getByText("Atendimento WhatsApp"));
    // n8n is a service component in the mock product
    expect(screen.getAllByText("n8n").length).toBeGreaterThan(0);
  });

  it("shows empty state when no products are available", async () => {
    server.use(
      http.get("/api/proxy/products/catalog/", () =>
        HttpResponse.json({ success: true, data: [], error: null })
      )
    );

    renderWithProviders(<CatalogPage />);
    await waitFor(() => {
      expect(screen.getByText(/nenhum serviço disponível/i)).toBeInTheDocument();
    });
  });
});
