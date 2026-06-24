import { screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import BackofficeAuditPage from "@/app/backoffice/audit/page";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/backoffice/audit",
}));

describe("BackofficeAuditPage", () => {
  it("renders page title", async () => {
    renderWithProviders(<BackofficeAuditPage />);
    await waitFor(() => expect(screen.getByText("Audit Log")).toBeTruthy());
  });

  it("shows audit log entry action", async () => {
    renderWithProviders(<BackofficeAuditPage />);
    await waitFor(() =>
      expect(screen.getByText("customer.created")).toBeTruthy()
    );
  });

  it("shows resource type in entry", async () => {
    renderWithProviders(<BackofficeAuditPage />);
    await waitFor(() => expect(screen.getByText("Customer")).toBeTruthy());
  });

  it("shows user email in entry", async () => {
    renderWithProviders(<BackofficeAuditPage />);
    await waitFor(() =>
      expect(screen.getByText("admin@papermoon.com")).toBeTruthy()
    );
  });

  it("renders resource type filter select", async () => {
    renderWithProviders(<BackofficeAuditPage />);
    await waitFor(() =>
      expect(screen.getByText("Todos os recursos")).toBeTruthy()
    );
  });

  it("shows empty state when no logs", async () => {
    const { http, HttpResponse } = await import("msw");
    const { server } = await import("../mocks/server");
    server.use(
      http.get("/api/proxy/admin/audit-logs/", () =>
        HttpResponse.json({ success: true, data: { count: 0, next: null, previous: null, results: [] }, error: null })
      )
    );
    renderWithProviders(<BackofficeAuditPage />);
    await waitFor(() =>
      expect(screen.getByText(/Nenhum registro encontrado/)).toBeTruthy()
    );
  });
});
