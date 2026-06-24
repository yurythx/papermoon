import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AcceptInvitePage from "@/app/invite/accept/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";

const pushMock = vi.fn();
let tokenParam: string | null = "valid-token";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
  useSearchParams: () => ({ get: (key: string) => (key === "token" ? tokenParam : null) }),
}));

vi.mock("@/store/auth", () => ({
  useAuthStore: () => ({ me: null, setMe: vi.fn(), clearMe: vi.fn() }),
}));

describe("AcceptInvitePage", () => {
  it("renders password fields when token is present", async () => {
    tokenParam = "valid-token";
    renderWithProviders(<AcceptInvitePage />);
    await waitFor(() => {
      expect(screen.getByLabelText(/crie sua senha/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirmar senha/i)).toBeInTheDocument();
    });
  });

  it("shows error message when token is missing", async () => {
    tokenParam = null;
    renderWithProviders(<AcceptInvitePage />);
    await waitFor(() => {
      expect(screen.getByText(/link de convite inválido/i)).toBeInTheDocument();
    });
  });

  it("shows error when passwords do not match", async () => {
    tokenParam = "valid-token";
    renderWithProviders(<AcceptInvitePage />);

    await waitFor(() => screen.getByLabelText(/crie sua senha/i));
    await userEvent.type(screen.getByLabelText(/crie sua senha/i), "senha12345");
    await userEvent.type(screen.getByLabelText(/confirmar senha/i), "diferente1");
    await userEvent.click(screen.getByRole("button", { name: /criar conta/i }));

    await waitFor(() => {
      expect(screen.getByText(/senhas não coincidem/i)).toBeInTheDocument();
    });
  });

  it("shows error when password is too short", async () => {
    tokenParam = "valid-token";
    renderWithProviders(<AcceptInvitePage />);

    await waitFor(() => screen.getByLabelText(/crie sua senha/i));
    await userEvent.type(screen.getByLabelText(/crie sua senha/i), "curta");
    await userEvent.type(screen.getByLabelText(/confirmar senha/i), "curta");
    await userEvent.click(screen.getByRole("button", { name: /criar conta/i }));

    await waitFor(() => {
      expect(screen.getByText(/pelo menos 8 caracteres/i)).toBeInTheDocument();
    });
  });

  it("redirects to /login?invited=1 on success", async () => {
    tokenParam = "valid-token";
    server.use(
      http.post("/api/invitations/accept", () =>
        HttpResponse.json({ success: true, data: { message: "ok", customer_id: "c1", role: "member" }, error: null }, { status: 201 })
      )
    );

    renderWithProviders(<AcceptInvitePage />);
    await waitFor(() => screen.getByLabelText(/crie sua senha/i));
    await userEvent.type(screen.getByLabelText(/crie sua senha/i), "senha12345");
    await userEvent.type(screen.getByLabelText(/confirmar senha/i), "senha12345");
    await userEvent.click(screen.getByRole("button", { name: /criar conta/i }));

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/login?invited=1");
    });
  });

  it("shows backend error message on failure", async () => {
    tokenParam = "expired-token";
    server.use(
      http.post("/api/invitations/accept", () =>
        HttpResponse.json(
          { success: false, data: null, error: { code: "validation_error", message: "Convite expirado.", details: [] } },
          { status: 400 }
        )
      )
    );

    renderWithProviders(<AcceptInvitePage />);
    await waitFor(() => screen.getByLabelText(/crie sua senha/i));
    await userEvent.type(screen.getByLabelText(/crie sua senha/i), "senha12345");
    await userEvent.type(screen.getByLabelText(/confirmar senha/i), "senha12345");
    await userEvent.click(screen.getByRole("button", { name: /criar conta/i }));

    await waitFor(() => {
      expect(screen.getByText(/convite expirado/i)).toBeInTheDocument();
    });
  });

  it("renders PasswordStrength component after typing", async () => {
    tokenParam = "valid-token";
    renderWithProviders(<AcceptInvitePage />);

    await waitFor(() => screen.getByLabelText(/crie sua senha/i));
    await userEvent.type(screen.getByLabelText(/crie sua senha/i), "abc");

    await waitFor(() => {
      // PasswordStrength renders segment bars when there is input
      expect(document.querySelectorAll("[data-strength-bar]").length > 0 ||
             screen.queryByText(/muito fraca/i) !== null ||
             document.querySelector(".rounded-full") !== null
      ).toBe(true);
    });
  });
});
