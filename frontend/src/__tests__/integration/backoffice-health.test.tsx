import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import HealthPage from "@/app/backoffice/health/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/backoffice/health",
}));

describe("HealthPage", () => {
  it("shows overall ok banner when all services are healthy", async () => {
    renderWithProviders(<HealthPage />);

    await waitFor(() => {
      expect(screen.getByText("Todos os serviços estão operacionais")).toBeInTheDocument();
    });
  });

  it("renders service cards for db, redis, celery", async () => {
    renderWithProviders(<HealthPage />);

    await waitFor(() => {
      expect(screen.getByText("PostgreSQL")).toBeInTheDocument();
      expect(screen.getByText("Redis")).toBeInTheDocument();
      expect(screen.getByText("Celery Workers")).toBeInTheDocument();
    });
  });

  it("shows all services as Operacional when backend returns ok", async () => {
    renderWithProviders(<HealthPage />);

    await waitFor(() => {
      const labels = screen.getAllByText("Operacional");
      expect(labels.length).toBe(3);
    });
  });

  it("shows error banner when backend is unreachable", async () => {
    server.use(
      http.get("/api/proxy/health/", () =>
        HttpResponse.json({ success: false, data: null, error: { code: "server_error", message: "Unavailable", details: [] } }, { status: 503 })
      )
    );

    renderWithProviders(<HealthPage />);

    await waitFor(() => {
      expect(screen.getByText(/não foi possível contatar/i)).toBeInTheDocument();
    });
  });

  it("shows degraded banner when a service is degraded", async () => {
    server.use(
      http.get("/api/proxy/health/", () =>
        HttpResponse.json({
          success: true,
          data: { db: "ok", redis: "degraded", celery: "ok" },
          error: null,
        })
      )
    );

    renderWithProviders(<HealthPage />);

    await waitFor(() => {
      expect(screen.getByText("Serviços operando em modo degradado")).toBeInTheDocument();
    });
  });
});
