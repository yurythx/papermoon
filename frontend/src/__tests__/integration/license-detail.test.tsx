import { screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import LicenseDetailPage from "@/app/dashboard/licenses/[id]/page";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/dashboard/licenses/lic1",
  useParams: () => ({ id: "lic1" }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("LicenseDetailPage", () => {
  it("renders product name", async () => {
    renderWithProviders(<LicenseDetailPage params={{ id: "lic1" }} />);
    // product_name appears in both h1 and info row — getAllByText
    await waitFor(() => expect(screen.getAllByText("Atendimento WhatsApp").length).toBeGreaterThanOrEqual(2));
  });

  it("shows license key", async () => {
    renderWithProviders(<LicenseDetailPage params={{ id: "lic1" }} />);
    await waitFor(() => expect(screen.getByText("lic-abc123")).toBeTruthy());
  });

  it("shows active status badge", async () => {
    renderWithProviders(<LicenseDetailPage params={{ id: "lic1" }} />);
    await waitFor(() => expect(screen.getAllByText("Ativo").length).toBeGreaterThan(0));
  });

  it("shows service accesses", async () => {
    renderWithProviders(<LicenseDetailPage params={{ id: "lic1" }} />);
    await waitFor(() => expect(screen.getByText("n8n")).toBeTruthy());
  });

  it("shows back link to licenses list", async () => {
    renderWithProviders(<LicenseDetailPage params={{ id: "lic1" }} />);
    await waitFor(() =>
      expect(screen.getByText("Minhas Licenças")).toBeTruthy()
    );
  });

  it("shows not found state for unknown license", async () => {
    const { http, HttpResponse } = await import("msw");
    const { server } = await import("../mocks/server");
    server.use(
      http.get("/api/proxy/client/licenses/:id/", () =>
        HttpResponse.json({ success: false, data: null, error: { code: "not_found", message: "Not found", details: [] } }, { status: 404 })
      )
    );
    renderWithProviders(<LicenseDetailPage params={{ id: "unknown" }} />);
    await waitFor(() =>
      expect(screen.getByText("Licença não encontrada.")).toBeTruthy()
    );
  });
});
