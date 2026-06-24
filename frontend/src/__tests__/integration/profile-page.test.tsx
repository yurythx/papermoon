import { screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import ProfilePage from "@/app/dashboard/profile/page";
import { renderWithProviders } from "../utils/render";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/dashboard/profile",
}));

describe("ProfilePage", () => {
  it("renders company name field", async () => {
    renderWithProviders(<ProfilePage />);
    await waitFor(() =>
      expect(screen.getByLabelText("Razão social")).toBeTruthy()
    );
  });

  it("shows CNPJ from API as readonly", async () => {
    renderWithProviders(<ProfilePage />);
    await waitFor(() => {
      const cnpjInput = screen.getByLabelText("CNPJ") as HTMLInputElement;
      expect(cnpjInput.readOnly).toBe(true);
    });
  });

  it("shows status badge", async () => {
    renderWithProviders(<ProfilePage />);
    await waitFor(() => expect(screen.getByText("Ativo")).toBeTruthy());
  });

  it("renders password change form", async () => {
    renderWithProviders(<ProfilePage />);
    await waitFor(() => {
      expect(screen.getByLabelText("Senha atual")).toBeTruthy();
      expect(screen.getByLabelText("Nova senha")).toBeTruthy();
      expect(screen.getByLabelText("Confirmar nova senha")).toBeTruthy();
    });
  });

  it("shows error when new password != confirm password", async () => {
    renderWithProviders(<ProfilePage />);
    await waitFor(() => screen.getByLabelText("Senha atual"));

    fireEvent.change(screen.getByLabelText("Senha atual"), { target: { value: "oldpass" } });
    fireEvent.change(screen.getByLabelText("Nova senha"), { target: { value: "newpass1" } });
    fireEvent.change(screen.getByLabelText("Confirmar nova senha"), { target: { value: "newpass2" } });
    fireEvent.submit(screen.getByRole("button", { name: "Alterar senha" }).closest("form")!);

    await waitFor(() =>
      expect(screen.getByText("As senhas não coincidem.")).toBeTruthy()
    );
  });

  it("shows error when new password is too short", async () => {
    renderWithProviders(<ProfilePage />);
    await waitFor(() => screen.getByLabelText("Senha atual"));

    fireEvent.change(screen.getByLabelText("Senha atual"), { target: { value: "oldpass" } });
    fireEvent.change(screen.getByLabelText("Nova senha"), { target: { value: "short" } });
    fireEvent.change(screen.getByLabelText("Confirmar nova senha"), { target: { value: "short" } });
    fireEvent.submit(screen.getByRole("button", { name: "Alterar senha" }).closest("form")!);

    await waitFor(() =>
      expect(screen.getByText(/mínimo 8 caracteres/i)).toBeTruthy()
    );
  });

  it("Salvar button is disabled when company name unchanged", async () => {
    renderWithProviders(<ProfilePage />);
    await waitFor(() => screen.getByLabelText("Razão social"));
    const btn = screen.getByRole("button", { name: "Salvar alterações" }) as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });
});
