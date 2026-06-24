import { NextRequest, NextResponse } from "next/server";
import { applyAuthCookies, djangoFetch, getAccessToken, getRefreshToken } from "@/lib/session";

type Context = { params: { path: string[] } };

async function proxy(req: NextRequest, { params }: Context): Promise<NextResponse> {
  const djangoPath = `/${params.path.join("/")}/`;
  const search = req.nextUrl.search;
  const fullPath = search ? `${djangoPath}${search}` : djangoPath;

  let access = getAccessToken();
  if (!access) {
    return NextResponse.json(
      { success: false, data: null, error: { code: "unauthenticated", message: "Não autenticado.", details: [] } },
      { status: 401 }
    );
  }

  const contentType = req.headers.get("content-type") ?? "";
  const isMultipart = contentType.startsWith("multipart/form-data");

  let body: BodyInit | undefined;
  let extraHeaders: Record<string, string> = {};
  if (["GET", "HEAD"].includes(req.method)) {
    body = undefined;
  } else if (isMultipart) {
    body = await req.arrayBuffer();
    extraHeaders = { "Content-Type": contentType };
  } else {
    body = await req.text();
  }

  let res = await djangoFetch(fullPath, { method: req.method, body, headers: extraHeaders }, access);

  // Transparent token refresh on 401
  if (res.status === 401) {
    const refresh = getRefreshToken();
    if (refresh) {
      const refreshRes = await djangoFetch("/auth/refresh/", {
        method: "POST",
        body: JSON.stringify({ refresh }),
      });

      if (refreshRes.ok) {
        const refreshData = await refreshRes.json();
        access = refreshData.data?.access as string;
        res = await djangoFetch(fullPath, { method: req.method, body, headers: extraHeaders }, access);

        const ct = res.headers.get("content-type") ?? "";
        let refreshedResponse: NextResponse;
        if (!ct.includes("application/json")) {
          const bytes = await res.arrayBuffer();
          const headers = new Headers();
          headers.set("Content-Type", ct || "application/octet-stream");
          const disposition = res.headers.get("content-disposition");
          if (disposition) headers.set("Content-Disposition", disposition);
          refreshedResponse = new NextResponse(bytes, { status: res.status, headers });
        } else {
          refreshedResponse = NextResponse.json(await res.json(), { status: res.status });
        }
        applyAuthCookies(refreshedResponse, access, refresh);
        return refreshedResponse;
      }
    }
  }

  // HTTP 204/205/304 must not carry a body (Fetch spec § null body status)
  const NULL_BODY_STATUSES = new Set([101, 103, 204, 205, 304]);
  if (NULL_BODY_STATUSES.has(res.status)) {
    return new NextResponse(null, { status: res.status });
  }

  const resContentType = res.headers.get("content-type") ?? "";

  // Pass through file downloads (CSV, PDF, etc.) with original headers intact
  if (!resContentType.includes("application/json")) {
    const bytes = await res.arrayBuffer();
    const headers = new Headers();
    headers.set("Content-Type", resContentType || "application/octet-stream");
    const disposition = res.headers.get("content-disposition");
    if (disposition) headers.set("Content-Disposition", disposition);
    return new NextResponse(bytes, { status: res.status, headers });
  }

  const responseBody = await res.json();
  return NextResponse.json(responseBody, { status: res.status });
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const PUT = proxy;
export const DELETE = proxy;
