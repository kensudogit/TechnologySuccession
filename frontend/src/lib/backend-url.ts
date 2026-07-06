/** サーバー側プロキシが Backend に接続する URL を解決する */
export function resolveBackendUrl(): string | null {
  if (process.env.COMBINED_DEPLOY === "1") {
    return "http://127.0.0.1:8080";
  }

  const explicit = process.env.BACKEND_URL?.trim();
  if (explicit) {
    const normalized = explicit.replace(/\/$/, "");
    if (
      normalized.includes("127.0.0.1") ||
      normalized.includes("localhost") ||
      normalized.endsWith(".railway.internal")
    ) {
      return normalized;
    }
    // Misconfigured: BACKEND_URL points at the public frontend URL
    if (normalized.includes(".up.railway.app")) {
      return "http://127.0.0.1:8080";
    }
    return normalized;
  }

  const candidates = [
    process.env.RAILWAY_BACKEND_URL,
    process.env.BACKEND_INTERNAL_URL,
  ];

  for (const raw of candidates) {
    const url = raw?.trim();
    if (!url) continue;
    if (url.includes("localhost") || url.includes("127.0.0.1")) continue;
    return url.replace(/\/$/, "");
  }

  if (process.env.RAILWAY_ENVIRONMENT) {
    const service = process.env.BACKEND_RAILWAY_SERVICE?.trim();
    const port = process.env.BACKEND_PORT?.trim() || "8080";
    if (service) {
      return `http://${service}.railway.internal:${port}`;
    }
  }

  const publicUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "";
  const isLocal =
    !publicUrl ||
    publicUrl.includes("localhost") ||
    publicUrl.includes("127.0.0.1");
  if (!isLocal) return publicUrl.replace(/\/$/, "");

  return null;
}
