const { createServer } = require("http");
const { parse } = require("url");
const next = require("next");

const port = parseInt(process.env.PORT || "3000", 10);
const hostname = "0.0.0.0";
const dev = process.env.NODE_ENV === "development";

function internalBackendBase() {
  const explicit = (process.env.BACKEND_URL || "").trim();
  if (explicit) return explicit.replace(/\/$/, "");
  const internalPort = process.env.INTERNAL_BACKEND_PORT || "18080";
  return `http://127.0.0.1:${internalPort}`;
}

function resolveBackendBase() {
  const explicit = (process.env.BACKEND_URL || "").trim();
  if (explicit) {
    const normalized = explicit.replace(/\/$/, "");
    if (normalized.includes(".up.railway.app") && !normalized.includes(".railway.internal")) {
      return internalBackendBase();
    }
    return normalized;
  }
  if (process.env.COMBINED_DEPLOY === "1") {
    return internalBackendBase();
  }
  return null;
}

function shouldProxy() {
  if (process.env.COMBINED_DEPLOY === "1") return true;
  const base = resolveBackendBase();
  return Boolean(
    base &&
      (base.includes("127.0.0.1") ||
        base.includes("localhost") ||
        base.endsWith(".railway.internal"))
  );
}

function backendPathFromRequest(pathname) {
  if (pathname.startsWith("/api/backend/") || pathname === "/api/backend") {
    return pathname.replace(/^\/api\/backend/, "") || "/";
  }
  if (pathname.startsWith("/backend/") || pathname === "/backend") {
    return pathname.replace(/^\/backend/, "") || "/";
  }
  if (pathname.startsWith("/api/proxy/") || pathname === "/api/proxy") {
    return pathname.replace(/^\/api\/proxy/, "") || "/";
  }
  return null;
}

async function readRequestBody(req) {
  const chunks = [];
  for await (const chunk of req) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

async function proxyToBackend(req, res, backendPath, search) {
  const base = resolveBackendBase() || internalBackendBase();
  const target = `${base}${backendPath}${search || ""}`;

  const headers = new Headers();
  for (const [key, value] of Object.entries(req.headers)) {
    if (!value || key === "host") continue;
    const lower = key.toLowerCase();
    if (lower === "accept-encoding" || lower === "connection") continue;
    headers.set(key, Array.isArray(value) ? value.join(", ") : value);
  }

  const init = { method: req.method, headers };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await readRequestBody(req);
  }

  try {
    const backendRes = await fetch(target, init);
    res.statusCode = backendRes.status;
    backendRes.headers.forEach((value, key) => {
      const lower = key.toLowerCase();
      if (lower === "transfer-encoding" || lower === "content-encoding") return;
      res.setHeader(key, value);
    });
    const body = Buffer.from(await backendRes.arrayBuffer());
    res.end(body);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Backend request failed";
    res.statusCode = 502;
    res.setHeader("content-type", "application/json");
    res.end(JSON.stringify({ detail: `Cannot reach backend at ${base}: ${message}` }));
  }
}

const app = next({ dev, hostname });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  createServer(async (req, res) => {
    const parsedUrl = parse(req.url, true);
    const backendPath = shouldProxy()
      ? backendPathFromRequest(parsedUrl.pathname || "/")
      : null;

    if (backendPath !== null) {
      await proxyToBackend(req, res, backendPath, parsedUrl.search);
      return;
    }

    await handle(req, res, parsedUrl);
  }).listen(port, hostname, () => {
    console.log(
      `> Ready on http://${hostname}:${port} (proxy=${shouldProxy() ? resolveBackendBase() : "off"})`
    );
  });
});
