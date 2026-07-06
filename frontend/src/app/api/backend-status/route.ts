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
        ? "Railway Frontend の Variables に BACKEND_URL=https://<backend>.up.railway.app を設定して再デプロイしてください。"
        : "ローカル開発では backend を port 8000 で起動するか、.env.local に BACKEND_URL を設定してください。",
  });
}
