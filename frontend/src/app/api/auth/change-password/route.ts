import { NextRequest, NextResponse } from "next/server";
import { djangoFetch, getAccessToken } from "@/lib/session";

export async function POST(req: NextRequest) {
  const access = getAccessToken();
  if (!access) {
    return NextResponse.json(
      { success: false, data: null, error: { code: "unauthorized", message: "Não autenticado.", details: [] } },
      { status: 401 }
    );
  }
  const body = await req.json();
  const django = await djangoFetch("/auth/change-password/", { method: "POST", body: JSON.stringify(body) }, access);
  const payload = await django.json();
  return NextResponse.json(payload, { status: django.status });
}
