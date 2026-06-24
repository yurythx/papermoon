import { NextRequest, NextResponse } from "next/server";

const DJANGO = process.env.DJANGO_INTERNAL_URL ?? "http://localhost:8000/api/v1";

export async function POST(req: NextRequest) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: { message: "Requisição inválida." } }, { status: 400 });
  }

  try {
    const res = await fetch(`${DJANGO}/contact/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();

    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }

    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { error: { message: "Erro ao enviar mensagem. Tente novamente." } },
      { status: 502 },
    );
  }
}
