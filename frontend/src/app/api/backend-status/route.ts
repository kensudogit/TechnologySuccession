import { NextResponse } from "next/server";

import { resolveBackendUrl } from "@/lib/backend-url";

export const dynamic = "force-dynamic";

export async function GET() {
  const backendUrl = resolveBackendUrl();
  const onRailway = Boolean(process.env.RAILWAY_ENVIRONMENT);

  return NextResponse.json({
    configured: Boolean(backendUrl),
    backend_url: backendUrl,
    on_railway: onRailway,
    hint: backendUrl
      ? null
      : onRailway
        ? "再デプロイしてください。frontend/railway.toml が Dockerfile.combined（UI+API 一体）をビルドします。BACKEND_URL の設定は不要です。"
        : "ローカル開発では docker compose up するか、frontend/.env.local に BACKEND_URL=http://localhost:8000 を設定してください。",
  });
}
