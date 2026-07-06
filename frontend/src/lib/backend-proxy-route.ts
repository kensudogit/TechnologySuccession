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
