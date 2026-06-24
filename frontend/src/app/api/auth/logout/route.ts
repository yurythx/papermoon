import { NextResponse } from "next/server";
import { clearAuthCookies, djangoFetch, getRefreshToken } from "@/lib/session";

export async function POST() {
  const refresh = getRefreshToken();

  if (refresh) {
    await djangoFetch("/auth/logout/", {
      method: "POST",
      body: JSON.stringify({ refresh }),
    }).catch(() => null);
  }

  const response = NextResponse.json({ success: true, data: null, error: null });
  clearAuthCookies(response);
  return response;
}
