import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import ForgotPasswordPage from "@/app/forgot-password/page";
import ResetPasswordPage from "@/app/reset-password/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

const mockPush = vi.fn();
const mockGet = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => ({ get: mockGet }),
}));

beforeEach(() => {
  mockPush.mockReset();
  mockGet.mockReset();
  // Default: params return null (forgot-password / invalid-link scenarios)
  mockGet.mockImplementation(() => null);
});

// ── ForgotPasswordPage ────────────────────────────────────────────────────────

describe("ForgotPasswordPage", () => {
  it("renders email form", () => {
    renderWithProviders(<ForgotPasswordPage />);
    expect(screen.getByPlaceholderText(/voce@empresa.com/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /enviar link/i })).toBeInTheDocument();
  });

  it("shows success state after submit", async () => {
    renderWithProviders(<ForgotPasswordPage />);
    fireEvent.change(screen.getByPlaceholderText(/voce@empresa.com/i), {
      target: { value: "owner@acme.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /enviar link/i }));

    await waitFor(() => {
      expect(screen.getByText(/verifique seu e-mail/i)).toBeInTheDocument();
    });
  });

  it("shows error on API failure", async () => {
    server.use(
      http.post("/api/auth/password-reset", () =>
        HttpResponse.json(
          { success: false, data: null, error: { code: "error", message: "Erro ao enviar.", details: [] } },
          { status: 400 }
        )
      )
    );

    renderWithProviders(<ForgotPasswordPage />);
    fireEvent.change(screen.getByPlaceholderText(/voce@empresa.com/i), {
      target: { value: "bad@email.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /enviar link/i }));

    await waitFor(() => {
      expect(screen.getByText(/erro ao enviar/i)).toBeInTheDocument();
    });
  });

  it("has link back to login", () => {
    renderWithProviders(<ForgotPasswordPage />);
    expect(screen.getByRole("link", { name: /voltar/i })).toHaveAttribute("href", "/login");
  });
});

// ── ResetPasswordPage ─────────────────────────────────────────────────────────

describe("ResetPasswordPage — invalid link (no uid/token)", () => {
  it("shows error when uid or token is missing", () => {
    mockGet.mockReturnValue(null);
    renderWithProviders(<ResetPasswordPage />);
    expect(screen.getByText(/link inválido/i)).toBeInTheDocument();
  });
});

describe("ResetPasswordPage — valid link", () => {
  beforeEach(() => {
    mockGet.mockImplementation((key: string) => {
      if (key === "uid") return "abc123";
      if (key === "token") return "tok456";
      return null;
    });
  });

  it("renders new-password form when uid and token are present", async () => {
    renderWithProviders(<ResetPasswordPage />);
    // password inputs aren't matched by ARIA role — use placeholder or button
    await screen.findByRole("button", { name: /redefinir senha/i });
    expect(screen.getByPlaceholderText(/mínimo 8 caracteres/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/repita a senha/i)).toBeInTheDocument();
  });

  it("shows mismatch error when passwords differ", async () => {
    renderWithProviders(<ResetPasswordPage />);
    await screen.findByRole("button", { name: /redefinir senha/i });
    const pwdInput = screen.getByPlaceholderText(/mínimo 8 caracteres/i);
    const confirmInput = screen.getByPlaceholderText(/repita a senha/i);

    fireEvent.change(pwdInput, { target: { value: "Senha123!" } });
    fireEvent.change(confirmInput, { target: { value: "Diferente!" } });
    fireEvent.click(screen.getByRole("button", { name: /redefinir senha/i }));

    expect(screen.getByText(/senhas não coincidem/i)).toBeInTheDocument();
  });

  it("resets password and redirects to /login?reset=1 on success", async () => {
    renderWithProviders(<ResetPasswordPage />);
    await screen.findByRole("button", { name: /redefinir senha/i });
    const pwdInput = screen.getByPlaceholderText(/mínimo 8 caracteres/i);
    const confirmInput = screen.getByPlaceholderText(/repita a senha/i);

    fireEvent.change(pwdInput, { target: { value: "NovaSenha123!" } });
    fireEvent.change(confirmInput, { target: { value: "NovaSenha123!" } });
    fireEvent.click(screen.getByRole("button", { name: /redefinir senha/i }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/login?reset=1");
    });
  });

  it("shows error when token is invalid", async () => {
    server.use(
      http.post("/api/auth/password-reset/confirm", () =>
        HttpResponse.json(
          { success: false, data: null, error: { code: "invalid_token", message: "Link inválido ou expirado.", details: [] } },
          { status: 400 }
        )
      )
    );

    renderWithProviders(<ResetPasswordPage />);
    await screen.findByRole("button", { name: /redefinir senha/i });
    const pwdInput = screen.getByPlaceholderText(/mínimo 8 caracteres/i);
    const confirmInput = screen.getByPlaceholderText(/repita a senha/i);

    fireEvent.change(pwdInput, { target: { value: "NovaSenha123!" } });
    fireEvent.change(confirmInput, { target: { value: "NovaSenha123!" } });
    fireEvent.click(screen.getByRole("button", { name: /redefinir senha/i }));

    await waitFor(() => {
      expect(screen.getByText(/link inválido ou expirado/i)).toBeInTheDocument();
    });
  });
});
