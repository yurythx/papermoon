"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { authService } from "@/lib/services";

export function useAuth() {
  const router = useRouter();
  const { me, setMe, isAdmin } = useAuthStore();

  async function login(email: string, password: string) {
    // BFF sets httpOnly cookies on success
    await authService.login(email, password);
    // Populate store with user profile
    const profile = await authService.me();
    setMe(profile);
    router.push("/dashboard");
  }

  return {
    login,
    me,
    isAdmin: isAdmin(),
  };
}
