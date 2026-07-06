import { clearToken, getToken } from "./auth";

/** ブラウザから Backend へ接続するベース URL */
export function getApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL || "";
  const isLocal =
    !configured ||
    configured.includes("localhost") ||
    configured.includes("127.0.0.1");

  // Railway 本番: ビルド時に localhost が入っている場合は同一オリジンのプロキシ経由
  if (typeof window !== "undefined" && isLocal) {
    return "/api/proxy";
  }
  return configured || "http://localhost:8000";
}

function buildHeaders(extra?: HeadersInit): HeadersInit {
  const headers: Record<string, string> = {
    ...(extra as Record<string, string>),
  };
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse(res: Response) {
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new Error("認証が必要です。ログインしてください。");
  }
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAuthStatus() {
  const res = await fetch(`${getApiBase()}/auth/status`);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ auth_enabled: boolean; openai_configured: boolean }>;
}

export async function login(username: string, password: string) {
  const res = await fetch(`${getApiBase()}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return handleResponse(res) as Promise<{ access_token: string; token_type: string }>;
}

export async function askQuestion(question: string, equipmentName?: string) {
  const res = await fetch(`${getApiBase()}/chat/ask`, {
    method: "POST",
    headers: buildHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ question, equipment_name: equipmentName }),
  });
  return handleResponse(res);
}

export async function getStats() {
  const res = await fetch(`${getApiBase()}/records/stats`, { headers: buildHeaders() });
  return handleResponse(res);
}

export async function uploadFile(endpoint: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${getApiBase()}${endpoint}`, {
    method: "POST",
    headers: buildHeaders(),
    body: form,
  });
  return handleResponse(res);
}

export async function runEval() {
  const res = await fetch(`${getApiBase()}/eval/run`, {
    method: "POST",
    headers: buildHeaders(),
  });
  return handleResponse(res);
}

export async function listRecords(equipmentName?: string) {
  const params = equipmentName ? `?equipment_name=${encodeURIComponent(equipmentName)}` : "";
  const res = await fetch(`${getApiBase()}/records/${params}`, { headers: buildHeaders() });
  return handleResponse(res);
}

export async function seedDatabase() {
  const res = await fetch(`${getApiBase()}/admin/seed`, {
    method: "POST",
    headers: buildHeaders(),
  });
  return handleResponse(res);
}
