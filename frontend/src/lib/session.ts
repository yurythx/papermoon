import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const DJANGO_URL = process.env.DJANGO_INTERNAL_URL ?? "http://localhost:8000/api/v1";

// Django monta health/contato fora do prefixo /api/v1 (core/urls.py) — o único
// caso assim hoje. DJANGO_URL sem o sufixo, pra rotas que precisam chamar algo
// fora de /api/v1 sem duplicar a string base em outro arquivo.
const DJANGO_ROOT_URL = DJANGO_URL.replace(/\/api\/v1\/?$/, "");

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

  // Sem isso, o fetch cache do Next.js 14 (App Router) pode reter respostas
  // antigas mesmo em rotas com `dynamic = "force-dynamic"` — esse fetch
  // reflete estado mutável do backend (config de SSO, sessão, etc.) e nunca
  // deve ser servido do cache.
  return fetch(`${DJANGO_URL}${path}`, { ...init, headers, cache: "no-store" });
}

// Mesma coisa que djangoFetch, mas para os poucos endpoints montados fora de
// /api/v1 (hoje só /health/) — usar djangoFetch para eles bateria em
// /api/v1/health/, que não existe.
export async function djangoRootFetch(path: string, init: RequestInit = {}): Promise<Response> {
  return fetch(`${DJANGO_ROOT_URL}${path}`, { ...init, cache: "no-store" });
}
