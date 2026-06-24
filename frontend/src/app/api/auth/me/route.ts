import { NextResponse } from "next/server";
import { applyAuthCookies, djangoFetch, getAccessToken, getRefreshToken } from "@/lib/session";

export async function GET() {
  let access = getAccessToken();

  if (!access) {
    return NextResponse.json(
      { success: false, data: null, error: { code: "unauthenticated", message: "Não autenticado.", details: [] } },
      { status: 401 }
    );
  }

  let res = await djangoFetch("/auth/me/", {}, access);

  if (res.status === 401) {
    const refresh = getRefreshToken();
    if (!refresh) {
      return NextResponse.json(
        { success: false, data: null, error: { code: "unauthenticated", message: "Sessão expirada.", details: [] } },
        { status: 401 }
      );
    }

    const refreshRes = await djangoFetch("/auth/refresh/", {
      method: "POST",
      body: JSON.stringify({ refresh }),
    });

    if (!refreshRes.ok) {
      return NextResponse.json(
        { success: false, data: null, error: { code: "session_expired", message: "Sessão expirada.", details: [] } },
        { status: 401 }
      );
    }

    const refreshData = await refreshRes.json();
    access = refreshData.data?.access as string;
    res = await djangoFetch("/auth/me/", {}, access);

    const payload = await res.json();
    const response = NextResponse.json(payload, { status: res.status });
    applyAuthCookies(response, access, refresh);
    return response;
  }

  const payload = await res.json();
  return NextResponse.json(payload, { status: res.status });
}
