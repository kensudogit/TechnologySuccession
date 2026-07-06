import { NextResponse } from "next/server";

function resolveBackendUrl(): string | null {
  const backendUrl = process.env.BACKEND_URL?.trim();
  if (backendUrl) return backendUrl.replace(/\/$/, "");

  const publicUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "";
  const isLocal =
    !publicUrl ||
    publicUrl.includes("localhost") ||
    publicUrl.includes("127.0.0.1");
  if (!isLocal) return publicUrl.replace(/\/$/, "");
  return null;
}

export async function GET() {
  const backendUrl = resolveBackendUrl();
  return NextResponse.json({
    configured: Boolean(backendUrl),
    backend_url: backendUrl,
    hint: backendUrl
      ? null
      : "Set BACKEND_URL on the frontend Railway service to the backend public URL.",
  });
}
