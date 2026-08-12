import { NextRequest, NextResponse } from "next/server";
import { djangoFetch, getClientIp } from "@/lib/session";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const django = await djangoFetch(
    "/invitations/accept/",
    { method: "POST", body: JSON.stringify(body) },
    undefined,
    getClientIp(req)
  );
  const payload = await django.json();
  return NextResponse.json(payload, { status: django.status });
}
