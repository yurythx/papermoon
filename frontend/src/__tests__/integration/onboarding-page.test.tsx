import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import OnboardingPage from "@/app/onboarding/page";
import { renderWithProviders } from "../utils/render";

// Hoist mock functions so they are available when vi.mock factories run
const { replaceMock, logoutMock, clearMeMock, setMeMock } = vi.hoisted(() => ({
  replaceMock: vi.fn(),
  logoutMock: vi.fn().mockResolvedValue(undefined),
  clearMeMock: vi.fn(),
  setMeMock: vi.fn(),
}));

let meState: { customer: object | null; user: { is_staff: boolean } } = {
  customer: null,
  user: { is_staff: false },
};

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
  usePathname: () => "/onboarding",
  useSearchParams: () => ({ get: () => null }),
}));

vi.mock("@/store/auth", () => ({
  useAuthStore: () => ({
    me: meState,
    setMe: setMeMock,
    clearMe: clearMeMock,
  }),
}));

vi.mock("@/lib/services", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/lib/services")>();
  return {
    ...original,
    authService: {
      ...original.authService,
      logout: logoutMock,
      me: vi.fn().mockResolvedValue({
        user: { id: "u1", email: "user@test.com", username: "user", is_staff: false },
        customer: null,
        role: null,
      }),
    },
  };
});

describe("OnboardingPage", () => {
  it("renders the waiting page heading", async () => {
    meState = { customer: null, user: { is_staff: false } };
    renderWithProviders(<OnboardingPage />);
    await waitFor(() => {
      expect(screen.getByText(/aguardando configuração/i)).toBeInTheDocument();
    });
  });

  it("shows the 3 onboarding steps", async () => {
    meState = { customer: null, user: { is_staff: false } };
    renderWithProviders(<OnboardingPage />);
    await waitFor(() => {
      expect(screen.getByText(/verifique seu e-mail/i)).toBeInTheDocument();
      expect(screen.getByText(/instalação na sua vps/i)).toBeInTheDocument();
      expect(screen.getByText(/acesse o dashboard/i)).toBeInTheDocument();
    });
  });

  it("shows polling indicator text", async () => {
    meState = { customer: null, user: { is_staff: false } };
    renderWithProviders(<OnboardingPage />);
    await waitFor(() => {
      const hasIndicator =
        screen.queryByText(/verificando status/i) !== null ||
        screen.queryByText(/verificação automática/i) !== null;
      expect(hasIndicator).toBe(true);
    });
  });

  it("redirects to /dashboard when customer is provisioned", async () => {
    meState = {
      customer: { id: "c1", company_name: "Acme", status: "active" },
      user: { is_staff: false },
    };
    replaceMock.mockClear();
    renderWithProviders(<OnboardingPage />);
    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("redirects to /backoffice for staff users", async () => {
    meState = { customer: null, user: { is_staff: true } };
    replaceMock.mockClear();
    renderWithProviders(<OnboardingPage />);
    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/backoffice");
    });
  });

  it("calls logout when clicking Sair", async () => {
    meState = { customer: null, user: { is_staff: false } };
    logoutMock.mockClear();
    renderWithProviders(<OnboardingPage />);

    await waitFor(() => screen.getByText(/sair da conta/i));
    await userEvent.click(screen.getByText(/sair da conta/i));

    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalled();
    });
  });

  it("shows 'Tentar acessar o dashboard' link", async () => {
    meState = { customer: null, user: { is_staff: false } };
    renderWithProviders(<OnboardingPage />);
    await waitFor(() => {
      expect(screen.getByText(/tentar acessar o dashboard/i)).toBeInTheDocument();
    });
  });
});
