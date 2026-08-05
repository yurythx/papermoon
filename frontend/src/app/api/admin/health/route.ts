import { NextResponse } from "next/server";
import { djangoRootFetch, getAccessToken } from "@/lib/session";

// Separado do /api/proxy/[...path] genérico de propósito: /health/ do Django
// vive fora do prefixo /api/v1 (core/urls.py), e o proxy genérico sempre
// monta a URL como {DJANGO_INTERNAL_URL}/api/v1/<path> — bateria em
// /api/v1/health/, que não existe (404). Ver docs/backend/api.md.
//
// A view Django (AllowAny, sem throttle — feita pra LB/monitoramento) não
// exige token; a checagem de sessão aqui é só pra manter consistente que
// só staff autenticado vê detalhe de infra pelo backoffice.
export async function GET() {
  if (!getAccessToken()) {
    return NextResponse.json(
      { success: false, data: null, error: { code: "unauthenticated", message: "Não autenticado.", details: [] } },
      { status: 401 }
    );
  }

  try {
    const res = await djangoRootFetch("/health/");
    const body = await res.json();
    return NextResponse.json(body, { status: res.status });
  } catch {
    return NextResponse.json(
      { success: false, data: null, error: { code: "upstream_unreachable", message: "Não foi possível contatar o backend.", details: [] } },
      { status: 502 }
    );
  }
}
