import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LoginPage from "@/app/login/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

// next/navigation must be mocked — not available outside Next.js runtime
const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
  usePathname: () => "/login",
  useSearchParams: () => ({ get: () => null }),
}));

// Zustand auth store — reset between tests
vi.mock("@/store/auth", () => {
  const setMe = vi.fn();
  const clearMe = vi.fn();
  return {
    useAuthStore: () => ({ me: null, setMe, clearMe, isAdmin: () => false }),
  };
});

describe("LoginPage", () => {
  it("renders email and password fields", () => {
    renderWithProviders(<LoginPage />);
    expect(screen.getByPlaceholderText("voce@empresa.com")).toBeInTheDocument();
    expect(screen.getByLabelText("Senha")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Entrar na conta" })).toBeInTheDocument();
  });

  it("redirects to /dashboard on successful login", async () => {
    renderWithProviders(<LoginPage />);

    await userEvent.type(screen.getByPlaceholderText("voce@empresa.com"), "owner@acme.com");
    await userEvent.type(screen.getByLabelText("Senha"), "demo123");
    await userEvent.click(screen.getByRole("button", { name: "Entrar na conta" }));

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("shows error message on failed login", async () => {
    server.use(
      http.post("/api/auth/login", () =>
        HttpResponse.json(
          { success: false, data: null, error: { code: "invalid_credentials", message: "Credenciais inválidas.", details: [] } },
          { status: 401 }
        )
      )
    );

    renderWithProviders(<LoginPage />);

    await userEvent.type(screen.getByPlaceholderText("voce@empresa.com"), "bad@user.com");
    await userEvent.type(screen.getByLabelText("Senha"), "wrongpass");
    await userEvent.click(screen.getByRole("button", { name: "Entrar na conta" }));

    await waitFor(() => {
      expect(screen.getByText(/credenciais inválidas/i)).toBeInTheDocument();
    });
  });

  it("disables submit button while loading", async () => {
    // Slow response to catch loading state
    server.use(
      http.post("/api/auth/login", async () => {
        await new Promise((r) => setTimeout(r, 100));
        return HttpResponse.json({ success: true, data: { message: "ok" }, error: null });
      })
    );

    renderWithProviders(<LoginPage />);
    await userEvent.type(screen.getByPlaceholderText("voce@empresa.com"), "owner@acme.com");
    await userEvent.type(screen.getByLabelText("Senha"), "demo123");
    await userEvent.click(screen.getByRole("button", { name: "Entrar na conta" }));

    expect(screen.getByRole("button", { name: "Entrando..." })).toBeDisabled();
  });
});
