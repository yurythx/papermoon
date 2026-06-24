import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import ApiKeysPage from "@/app/dashboard/api-keys/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/dashboard/api-keys",
  useSearchParams: () => ({ get: () => null }),
}));

// clipboard.writeText not available in jsdom
Object.assign(navigator, {
  clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
});

describe("ApiKeysPage", () => {
  it("renders active and revoked keys after loading", async () => {
    renderWithProviders(<ApiKeysPage />);

    await waitFor(() => {
      expect(screen.getByText("test-key-abc123")).toBeInTheDocument();
    });

    expect(screen.getByText(/ativas/i)).toBeInTheDocument();
    expect(screen.getByText(/revogadas/i)).toBeInTheDocument();
  });

  it("shows copy and revoke buttons only for active keys", async () => {
    renderWithProviders(<ApiKeysPage />);

    await waitFor(() => screen.getByText("test-key-abc123"));

    const copyButtons = screen.getAllByRole("button", { name: /copiar/i });
    expect(copyButtons).toHaveLength(1);

    const revokeButtons = screen.getAllByRole("button", { name: /revogar/i });
    expect(revokeButtons).toHaveLength(1);
  });

  it("shows empty state when there are no active keys", async () => {
    server.use(
      http.get("/api/proxy/client/api-keys/", () =>
        HttpResponse.json({ success: true, data: [], error: null })
      )
    );

    renderWithProviders(<ApiKeysPage />);

    await waitFor(() => {
      expect(screen.getByText(/nenhuma api key ativa/i)).toBeInTheDocument();
    });
  });

  it("highlights newly created key", async () => {
    // Override GET to include the new key so it appears after invalidation
    server.use(
      http.get("/api/proxy/client/api-keys/", () =>
        HttpResponse.json({
          success: true,
          data: [
            { id: "key1", key: "test-key-abc123", is_active: true, created_at: "2024-01-01T00:00:00Z", revoked_at: null },
            { id: "key3", key: "new-key-generated", is_active: true, created_at: "2024-06-10T00:00:00Z", revoked_at: null },
          ],
          error: null,
        })
      )
    );

    renderWithProviders(<ApiKeysPage />);
    await waitFor(() => screen.getByText("test-key-abc123"));

    const generateBtn = screen.getByRole("button", { name: /gerar nova chave/i });
    fireEvent.click(generateBtn);

    await waitFor(() => {
      expect(screen.getByText("new-key-generated")).toBeInTheDocument();
    });
  });

  it("shows instruction block with validate-key endpoint info", async () => {
    renderWithProviders(<ApiKeysPage />);
    await waitFor(() => screen.getByText("test-key-abc123"));

    expect(screen.getByText(/como usar sua api key/i)).toBeInTheDocument();
    expect(screen.getByText(/validate-key/i)).toBeInTheDocument();
  });
});
