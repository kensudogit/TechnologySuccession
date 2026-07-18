import { NextRequest, NextResponse } from "next/server";

import { resolveBackendUrl } from "@/lib/backend-url";

export const dynamic = "force-dynamic";

type RouteParams = { path?: string[] };

async function resolvePath(
  params: RouteParams | Promise<RouteParams>
): Promise<string[]> {
  const resolved = await Promise.resolve(params);
  return resolved.path ?? [];
}

async function proxyRequest(req: NextRequest, pathSegments: string[]) {
  const base = resolveBackendUrl();
  if (!base) {
    return NextResponse.json(
      {
        detail:
          "BACKEND_URL is not configured on the frontend Railway service. " +
          "Set BACKEND_URL to your backend public URL, e.g. https://<backend>.up.railway.app " +
          "or BACKEND_RAILWAY_SERVICE=<backend-service-name> for private networking.",
      },
      { status: 503 }
    );
  }

  const path = pathSegments.join("/");
  const target = `${base}/${path}${req.nextUrl.search}`;

  const headers = new Headers();
  const auth = req.headers.get("authorization");
  const contentType = req.headers.get("content-type");
  if (auth) headers.set("authorization", auth);
  if (contentType) headers.set("content-type", contentType);

  const init: RequestInit = {
    method: req.method,
    headers,
    redirect: "manual",
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.arrayBuffer();
  }

  const controller = new AbortController();
  // 評価など長時間処理向け（既定の短いタイムアウトを避ける）
  const timeoutMs = path.startsWith("eval/") ? 240_000 : 60_000;
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(target, { ...init, signal: controller.signal });
    const responseHeaders = new Headers();
    const resType = res.headers.get("content-type");
    if (resType) responseHeaders.set("content-type", resType);

    const location = res.headers.get("location");
    if (location && (location.includes("127.0.0.1") || location.includes("localhost"))) {
      try {
        const parsed = new URL(location);
        responseHeaders.set("location", `/api/backend${parsed.pathname}${parsed.search}`);
      } catch {
        // ignore
      }
    }

    return new NextResponse(res.body, {
      status: res.status,
      headers: responseHeaders,
    });
  } catch (error) {
    const aborted = error instanceof Error && error.name === "AbortError";
    return NextResponse.json(
      {
        detail: aborted
          ? "Backend API の応答がタイムアウトしました。評価は時間がかかる場合があります。"
          : "Backend API に接続できません。しばらく待ってから再読み込みしてください。",
      },
      { status: aborted ? 504 : 502 }
    );
  } finally {
    clearTimeout(timer);
  }
}

type HandlerContext = { params: RouteParams | Promise<RouteParams> };

export async function GET(req: NextRequest, context: HandlerContext) {
  return proxyRequest(req, await resolvePath(context.params));
}

export async function POST(req: NextRequest, context: HandlerContext) {
  return proxyRequest(req, await resolvePath(context.params));
}

export async function PUT(req: NextRequest, context: HandlerContext) {
  return proxyRequest(req, await resolvePath(context.params));
}

export async function DELETE(req: NextRequest, context: HandlerContext) {
  return proxyRequest(req, await resolvePath(context.params));
}

export async function PATCH(req: NextRequest, context: HandlerContext) {
  return proxyRequest(req, await resolvePath(context.params));
}
