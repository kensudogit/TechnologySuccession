const { createServer, request: httpRequest } = require("http");
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

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function stripHopHeaders(headers) {
  const out = { ...headers };
  delete out.host;
  delete out.connection;
  delete out["accept-encoding"];
  delete out["x-forwarded-proto"];
  delete out["x-forwarded-host"];
  delete out["x-forwarded-for"];
  delete out.forwarded;
  return out;
}

function rewriteLocationHeader(location, backendPathPrefix) {
  if (!location) return location;
  try {
    const parsed = new URL(location, internalBackendBase());
    if (
      parsed.hostname === "127.0.0.1" ||
      parsed.hostname === "localhost" ||
      parsed.hostname.endsWith(".railway.internal")
    ) {
      return `${backendPathPrefix}${parsed.pathname}${parsed.search}`;
    }
  } catch {
    // keep original
  }
  return location;
}

function pipeResponse(backendRes, res, backendPathPrefix) {
  return new Promise((resolve, reject) => {
    res.statusCode = backendRes.statusCode || 502;
    for (const [key, value] of Object.entries(backendRes.headers)) {
      if (!value) continue;
      const lower = key.toLowerCase();
      if (lower === "transfer-encoding" || lower === "content-encoding") continue;
      if (lower === "location") {
        const rewritten = rewriteLocationHeader(
          Array.isArray(value) ? value[0] : value,
          backendPathPrefix
        );
        res.setHeader("location", rewritten);
        continue;
      }
      res.setHeader(key, value);
    }
    backendRes.body.pipe(res);
    backendRes.body.on("end", resolve);
    backendRes.body.on("error", reject);
    res.on("error", reject);
  });
}

function proxyOnce(targetUrl, req, body) {
  return new Promise((resolve, reject) => {
    const target = new URL(targetUrl);
    const headers = stripHopHeaders(req.headers);

    const options = {
      hostname: target.hostname,
      port: target.port,
      path: `${target.pathname}${target.search}`,
      method: req.method,
      headers,
    };

    const proxyReq = httpRequest(options, (proxyRes) => {
      resolve({
        statusCode: proxyRes.statusCode || 502,
        headers: proxyRes.headers,
        body: proxyRes,
      });
    });

    proxyReq.on("error", reject);
    proxyReq.setTimeout(15000, () => {
      proxyReq.destroy(new Error("Backend request timeout"));
    });

    if (body && body.length > 0) {
      proxyReq.end(body);
    } else {
      proxyReq.end();
    }
  });
}

async function proxyToBackend(req, res, backendPath, search) {
  const base = resolveBackendBase() || internalBackendBase();
  const target = `${base}${backendPath}${search || ""}`;
  const body =
    req.method !== "GET" && req.method !== "HEAD" ? await readRequestBody(req) : null;
  const prefix = (req.url || "").includes("/api/backend")
    ? "/api/backend"
    : (req.url || "").includes("/api/proxy")
      ? "/api/proxy"
      : "/backend";

  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const backendRes = await proxyOnce(target, req, body);
      await pipeResponse(backendRes, res, prefix);
      return;
    } catch (error) {
      if (attempt === 2) {
        res.statusCode = 502;
        res.setHeader("content-type", "application/json");
        res.end(
          JSON.stringify({
            detail: "Backend API に接続できません。しばらく待ってから再読み込みしてください。",
          })
        );
        return;
      }
      await sleep(300 * (attempt + 1));
    }
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
