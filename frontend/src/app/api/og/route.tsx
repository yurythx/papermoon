import { ImageResponse } from "next/og";
import type { NextRequest } from "next/server";

export const runtime = "edge";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const title = searchParams.get("title") ?? "PaperMoon";
  const desc =
    searchParams.get("desc") ?? "Infraestrutura de TI gerenciada para a sua empresa.";
  const tag = searchParams.get("tag") ?? "";

  return new ImageResponse(
    (
      <div
        style={{
          width: 1200,
          height: 630,
          display: "flex",
          flexDirection: "column",
          background: "#0F172A",
          padding: "64px 72px",
          position: "relative",
        }}
      >
        {/* accent bar */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: 6,
            background: "linear-gradient(90deg, #FBBF24 0%, #F59E0B 100%)",
          }}
        />

        {/* logo */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            marginBottom: 48,
          }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              background: "linear-gradient(135deg, #FBBF24, #F59E0B)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <div style={{ color: "#0F172A", fontSize: 20, fontWeight: 700 }}>P</div>
          </div>
          <div style={{ color: "#e2e8f0", fontSize: 22, fontWeight: 700, letterSpacing: -0.5 }}>
            PaperMoon
          </div>
        </div>

        {/* tag */}
        {tag && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              marginBottom: 20,
            }}
          >
            <div
              style={{
                background: "rgba(251,191,36,0.16)",
                border: "1px solid rgba(251,191,36,0.35)",
                borderRadius: 6,
                padding: "4px 12px",
                color: "#FBBF24",
                fontSize: 14,
                fontWeight: 600,
                letterSpacing: 0.3,
              }}
            >
              {tag}
            </div>
          </div>
        )}

        {/* title */}
        <div
          style={{
            color: "#f1f5f9",
            fontSize: title.length > 30 ? 52 : 64,
            fontWeight: 800,
            lineHeight: 1.1,
            letterSpacing: -1.5,
            marginBottom: 24,
            flex: 1,
          }}
        >
          {title}
        </div>

        {/* description */}
        <div
          style={{
            color: "#94a3b8",
            fontSize: 24,
            lineHeight: 1.5,
            maxWidth: 900,
            marginBottom: 48,
          }}
        >
          {desc.length > 120 ? desc.slice(0, 117) + "…" : desc}
        </div>

        {/* footer */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            borderTop: "1px solid rgba(255,255,255,0.08)",
            paddingTop: 24,
          }}
        >
          <div style={{ color: "#FBBF24", fontSize: 15, fontWeight: 600 }}>
            papermoon.com.br
          </div>
          <div style={{ color: "#334155", fontSize: 15 }}>·</div>
          <div style={{ color: "#475569", fontSize: 15 }}>
            Infraestrutura de TI para empresas
          </div>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    }
  );
}
