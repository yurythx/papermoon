import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { MeResponse } from "@/types";

// Tokens live in httpOnly cookies managed by the BFF — never stored here.
// Only `me` is persisted to avoid a /auth/me round-trip on every page load.
interface AuthState {
  me: MeResponse | null;
  setMe: (me: MeResponse) => void;
  clearMe: () => void;
  isAdmin: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      me: null,

      setMe: (me) => set({ me }),

      clearMe: () => set({ me: null }),

      isAdmin: () => get().me?.user.is_staff ?? false,
    }),
    {
      name: "papermoon-auth",
      partialize: (state) => ({ me: state.me }),
    }
  )
);
