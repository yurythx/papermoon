import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const DJANGO_URL = process.env.DJANGO_INTERNAL_URL ?? "http://localhost:8000/api/v1";

export const ACCESS_COOKIE = "rs_access";
export const REFRESH_COOKIE = "rs_refresh";

// SECURE_COOKIES=false disables the Secure flag for local Docker (HTTP).
// In real production (HTTPS), omit SECURE_COOKIES so it defaults to true.
const isProd =
  process.env.NODE_ENV === "production" && process.env.SECURE_COOKIES !== "false";

const COOKIE_BASE = {
  httpOnly: true,
  secure: isProd,
  sameSite: "strict" as const,
  path: "/",
};

// Write cookies onto a NextResponse — the only reliable way in Next.js 14 Route Handlers
export function applyAuthCookies(res: NextResponse, access: string, refresh: string): NextResponse {
  res.cookies.set(ACCESS_COOKIE, access, { ...COOKIE_BASE, maxAge: 60 * 60 });
  res.cookies.set(REFRESH_COOKIE, refresh, { ...COOKIE_BASE, maxAge: 60 * 60 * 24 * 7 });
  return res;
}

export function clearAuthCookies(res: NextResponse): NextResponse {
  res.cookies.delete(ACCESS_COOKIE);
  res.cookies.delete(REFRESH_COOKIE);
  return res;
}

// Read cookies from the incoming request (works fine in Route Handlers)
export function getAccessToken(): string | undefined {
  return cookies().get(ACCESS_COOKIE)?.value;
}

export function getRefreshToken(): string | undefined {
  return cookies().get(REFRESH_COOKIE)?.value;
}

// Direct call to Django — used only from server-side BFF routes
export async function djangoFetch(
  path: string,
  init: RequestInit = {},
  accessToken?: string
): Promise<Response> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

  return fetch(`${DJANGO_URL}${path}`, { ...init, headers });
}
