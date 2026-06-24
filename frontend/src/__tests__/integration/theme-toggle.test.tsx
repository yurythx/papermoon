import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { renderWithProviders } from "../utils/render";

const mockSetTheme = vi.fn();
let currentTheme = "dark";

vi.mock("next-themes", () => ({
  useTheme: () => ({ theme: currentTheme, resolvedTheme: currentTheme, setTheme: mockSetTheme }),
}));

describe("ThemeToggle", () => {
  beforeEach(() => {
    currentTheme = "dark";
    mockSetTheme.mockClear();
  });

  it("renders a button after mount", async () => {
    renderWithProviders(<ThemeToggle />);
    await waitFor(() => {
      expect(screen.getByRole("button")).toBeInTheDocument();
    });
  });

  it("shows aria-label to activate light mode when in dark mode", async () => {
    currentTheme = "dark";
    renderWithProviders(<ThemeToggle />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Ativar modo claro" })).toBeInTheDocument();
    });
  });

  it("shows aria-label to activate dark mode when in light mode", async () => {
    currentTheme = "light";
    renderWithProviders(<ThemeToggle />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Ativar modo escuro" })).toBeInTheDocument();
    });
  });

  it("calls setTheme('light') when clicking in dark mode", async () => {
    currentTheme = "dark";
    renderWithProviders(<ThemeToggle />);
    await waitFor(() => screen.getByRole("button"));
    fireEvent.click(screen.getByRole("button"));
    expect(mockSetTheme).toHaveBeenCalledWith("light");
    expect(mockSetTheme).toHaveBeenCalledTimes(1);
  });

  it("calls setTheme('dark') when clicking in light mode", async () => {
    currentTheme = "light";
    renderWithProviders(<ThemeToggle />);
    await waitFor(() => screen.getByRole("button"));
    fireEvent.click(screen.getByRole("button"));
    expect(mockSetTheme).toHaveBeenCalledWith("dark");
    expect(mockSetTheme).toHaveBeenCalledTimes(1);
  });

  it("applies custom className to the button", async () => {
    renderWithProviders(<ThemeToggle className="extra-class" />);
    await waitFor(() => {
      expect(screen.getByRole("button")).toHaveClass("extra-class");
    });
  });

  it("renders hidden placeholder before mount (SSR safety)", () => {
    // The aria-hidden div is rendered before useEffect runs.
    // After mount it is replaced by the button, so we only verify
    // the component mounts without throwing.
    expect(() => renderWithProviders(<ThemeToggle />)).not.toThrow();
  });
});
