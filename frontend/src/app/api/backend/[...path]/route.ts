import { NextRequest } from "next/server";

import {
  DELETE as proxyDelete,
  GET as proxyGet,
  PATCH as proxyPatch,
  POST as proxyPost,
  PUT as proxyPut,
} from "@/lib/backend-proxy-route";

type RouteParams = { path?: string[] };
type HandlerContext = { params: RouteParams | Promise<RouteParams> };

export const dynamic = "force-dynamic";
/** 評価・シードなど長時間 API 向け（秒） */
export const maxDuration = 300;

export async function GET(req: NextRequest, context: HandlerContext) {
  return proxyGet(req, context);
}

export async function POST(req: NextRequest, context: HandlerContext) {
  return proxyPost(req, context);
}

export async function PUT(req: NextRequest, context: HandlerContext) {
  return proxyPut(req, context);
}

export async function DELETE(req: NextRequest, context: HandlerContext) {
  return proxyDelete(req, context);
}

export async function PATCH(req: NextRequest, context: HandlerContext) {
  return proxyPatch(req, context);
}
