import { NextRequest, NextResponse } from "next/server";

import { NextRequest, NextResponse } from "next/server";

function resolveBackendUrl(): string | null {
  const backendUrl = process.env.BACKEND_URL?.trim();
  if (backendUrl) return backendUrl.replace(/\/$/, "");

  const publicUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "";
  const isLocal =
    !publicUrl ||
    publicUrl.includes("localhost") ||
    publicUrl.includes("127.0.0.1");

  // サーバー側プロキシでは localhost を使わない（ビルド時のデフォルト値を除外）
  if (!isLocal) return publicUrl.replace(/\/$/, "");
  return null;
}

async function proxyRequest(req: NextRequest, pathSegments: string[]) {
  const base = resolveBackendUrl();
  if (!base) {
    return NextResponse.json(
      {
        detail:
          "BACKEND_URL is not configured on the frontend Railway service. " +
          "Set BACKEND_URL to your backend public URL (e.g. https://<backend>.up.railway.app).",
      },
      { status: 503 }
    );
  }

  const path = pathSegments.join("/");
  const target = `${base.replace(/\/$/, "")}/${path}${req.nextUrl.search}`;

  const headers = new Headers();
  const auth = req.headers.get("authorization");
  const contentType = req.headers.get("content-type");
  if (auth) headers.set("authorization", auth);
  if (contentType) headers.set("content-type", contentType);

  const init: RequestInit = {
    method: req.method,
    headers,
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.arrayBuffer();
  }

  try {
    const res = await fetch(target, init);
    const responseHeaders = new Headers();
    const resType = res.headers.get("content-type");
    if (resType) responseHeaders.set("content-type", resType);

    return new NextResponse(res.body, {
      status: res.status,
      headers: responseHeaders,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Backend request failed";
    return NextResponse.json(
      { detail: `Cannot reach backend at ${base}: ${message}` },
      { status: 502 }
    );
  }
}

export async function GET(
  req: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(req, params.path);
}

export async function POST(
  req: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(req, params.path);
}

export async function PUT(
  req: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(req, params.path);
}

export async function DELETE(
  req: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(req, params.path);
}

export async function PATCH(
  req: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(req, params.path);
}
