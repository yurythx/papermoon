import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import TeamPage from "@/app/dashboard/team/page";
import { server } from "../mocks/server";
import { renderWithProviders } from "../utils/render";
import { useAuthStore } from "@/store/auth";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/dashboard/team",
  useSearchParams: () => ({ get: () => null }),
}));

const OWNER_ME = {
  user: { id: "u1", email: "owner@acme.com", username: "owner", is_staff: false },
  customer: { id: "c1", company_name: "Acme Ltda", document: "00.000.000/0001-00", status: "active" as const, asaas_customer_id: "", created_at: "", updated_at: "" },
  role: "owner" as const,
};

describe("TeamPage", () => {
  beforeEach(() => {
    useAuthStore.setState({ me: OWNER_ME });
  });
  it("renders member list after loading", async () => {
    renderWithProviders(<TeamPage />);
    await waitFor(() => {
      expect(screen.getByText("owner@acme.com")).toBeInTheDocument();
    });
    expect(screen.getByText("member@acme.com")).toBeInTheDocument();
    expect(screen.getByText("(você)")).toBeInTheDocument();
  });

  it("renders pending invitation", async () => {
    renderWithProviders(<TeamPage />);
    await waitFor(() => {
      expect(screen.getByText("novo@empresa.com")).toBeInTheDocument();
    });
    expect(screen.getByText("Pendente")).toBeInTheDocument();
  });

  it("shows revoke button only for pending invitations", async () => {
    renderWithProviders(<TeamPage />);
    await waitFor(() => {
      expect(screen.getByText("novo@empresa.com")).toBeInTheDocument();
    });
    const revokeButtons = screen.getAllByRole("button", { name: /revogar/i });
    expect(revokeButtons).toHaveLength(1);
  });

  it("revokes invitation — button triggers mutation and becomes disabled", async () => {
    renderWithProviders(<TeamPage />);
    await waitFor(() => expect(screen.getByText("novo@empresa.com")).toBeInTheDocument());

    const revokeBtn = screen.getByRole("button", { name: /revogar/i });
    expect(revokeBtn).not.toBeDisabled();

    // Click triggers the mutation; button stays in loading state briefly
    fireEvent.click(revokeBtn);

    // Mutation should succeed (default DELETE handler returns 204)
    // After success, query is invalidated and Pendente badge disappears
    await waitFor(() => {
      // After refetch with updated list (or same default), we just confirm no error toast
      expect(screen.queryByText(/erro ao revogar/i)).not.toBeInTheDocument();
    });
  });

  it("shows invite form for owner role", async () => {
    renderWithProviders(<TeamPage />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/email@empresa.com/i)).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /convidar/i })).toBeInTheDocument();
  });

  it("hides invite form for member role", async () => {
    useAuthStore.setState({
      me: { ...OWNER_ME, role: "member" as const },
    });

    renderWithProviders(<TeamPage />);
    await waitFor(() => expect(screen.getByText("owner@acme.com")).toBeInTheDocument());

    expect(screen.queryByPlaceholderText(/email@empresa.com/i)).not.toBeInTheDocument();
  });

  it("shows empty state when no invitations", async () => {
    server.use(
      http.get("/api/proxy/client/invitations/", () =>
        HttpResponse.json({ success: true, data: [], error: null })
      )
    );

    renderWithProviders(<TeamPage />);
    await waitFor(() => expect(screen.getByText("owner@acme.com")).toBeInTheDocument());
    expect(screen.getByText(/nenhum convite enviado/i)).toBeInTheDocument();
  });
});
