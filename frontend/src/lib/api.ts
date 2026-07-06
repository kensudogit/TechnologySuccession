import { clearToken, getToken } from "./auth";

/** ブラウザから Backend へ接続するベース URL */
export function getApiBase(): string {
  const publicBase = (process.env.NEXT_PUBLIC_API_BASE_URL || "").trim();

  if (typeof window !== "undefined") {
    // 分離デプロイ: 別サービスの Backend 公開 URL を直接利用
    if (
      publicBase.startsWith("https://") &&
      !publicBase.includes("localhost") &&
      !publicBase.includes("127.0.0.1")
    ) {
      return publicBase.replace(/\/$/, "");
    }
    // 一体デプロイ / プロキシ経由
    return "/api/backend";
  }

  return publicBase || "/api/backend";
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

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function apiFetch(url: string, init?: RequestInit, retries = 3): Promise<Response> {
  let lastError: unknown;
  for (let attempt = 0; attempt < retries; attempt += 1) {
    try {
      const res = await globalThis.fetch(url, init);
      if (res.status !== 502 && res.status !== 503) {
        return res;
      }
      if (attempt === retries - 1) {
        return res;
      }
    } catch (error) {
      lastError = error;
      if (attempt === retries - 1) {
        throw error instanceof TypeError && error.message === "Failed to fetch"
          ? new Error("Backend API に接続できません。しばらく待ってからページを再読み込みしてください。")
          : error;
      }
    }
    await sleep(400 * (attempt + 1));
  }
  throw lastError instanceof Error ? lastError : new Error("API request failed");
}

function formatApiError(status: number, detail: string): string {
  if (
    status === 502 ||
    detail.includes("127.0.0.1") ||
    detail.includes("localhost") ||
    detail.includes("Cannot reach backend")
  ) {
    return "Backend API に接続できません。しばらく待ってからページを再読み込みしてください。";
  }
  if (status === 401) {
    return "認証が必要です。ログインしてください。";
  }
  return detail;
}

async function handleResponse(res: Response, options?: { allowUnauthorized?: boolean }) {
  if (res.status === 401 && !options?.allowUnauthorized) {
    clearToken();
    const text = await res.text();
    let detail = "認証が必要です。ログインしてください。";
    try {
      const json = JSON.parse(text) as { detail?: string };
      if (json.detail === "Not authenticated" || json.detail === "Token expired" || json.detail === "Invalid token") {
        detail = "認証が必要です。ログインしてください。";
      } else if (json.detail) {
        detail = json.detail;
      }
    } catch {
      // keep default detail
    }
    throw new Error(detail);
  }
  if (!res.ok) {
    const text = await res.text();
    try {
      const json = JSON.parse(text) as { detail?: string };
      throw new Error(formatApiError(res.status, json.detail ?? text));
    } catch (e) {
      if (e instanceof SyntaxError) throw new Error(formatApiError(res.status, text));
      throw e;
    }
  }
  return res.json();
}

export async function getAuthStatus() {
  const res = await apiFetch(`${getApiBase()}/auth/status`);
  return handleResponse(res) as Promise<{
    auth_enabled: boolean;
    openai_configured: boolean;
  }>;
}

export async function login(username: string, password: string) {
  const res = await apiFetch(`${getApiBase()}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return handleResponse(res, { allowUnauthorized: true }) as Promise<{
    access_token: string;
    token_type: string;
  }>;
}

export async function askQuestion(question: string, equipmentName?: string) {
  const res = await apiFetch(`${getApiBase()}/chat/ask`, {
    method: "POST",
    headers: buildHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ question, equipment_name: equipmentName }),
  });
  return handleResponse(res);
}

export async function getStats() {
  const res = await apiFetch(`${getApiBase()}/records/stats`, { headers: buildHeaders() });
  return handleResponse(res);
}

export async function uploadFile(endpoint: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await apiFetch(`${getApiBase()}${endpoint}`, {
    method: "POST",
    headers: buildHeaders(),
    body: form,
  });
  return handleResponse(res);
}

export async function runEval() {
  const res = await apiFetch(`${getApiBase()}/eval/run`, {
    method: "POST",
    headers: buildHeaders(),
  });
  return handleResponse(res);
}

export async function listRecords(equipmentName?: string) {
  const params = equipmentName ? `?equipment_name=${encodeURIComponent(equipmentName)}` : "";
  const res = await apiFetch(`${getApiBase()}/records${params}`, { headers: buildHeaders() });
  return handleResponse(res);
}

export async function seedDatabase() {
  const res = await apiFetch(`${getApiBase()}/admin/seed`, {
    method: "POST",
    headers: buildHeaders(),
  });
  return handleResponse(res);
}

export type TestSuite = "unit" | "integration" | "all";

export type TestCaseResult = {
  name: string;
  outcome: string;
  duration: number;
  message: string | null;
};

export type TestClassResult = {
  module: string;
  class_name: string;
  tests: TestCaseResult[];
  passed: number;
  failed: number;
  skipped: number;
  total: number;
};

export type TestRunSummary = {
  total: number;
  passed: number;
  failed: number;
  skipped: number;
  duration_sec: number;
  exit_code: number;
};

export type TestRunDetail = {
  run_id: string;
  suite: TestSuite;
  status: string;
  summary: TestRunSummary;
  duration_sec: number;
  created_at: string;
  classes?: TestClassResult[];
};

export async function runTests(suite: TestSuite = "unit") {
  const res = await apiFetch(`${getApiBase()}/tests/run?suite=${suite}`, {
    method: "POST",
    headers: buildHeaders(),
  });
  return handleResponse(res) as Promise<TestRunDetail>;
}

export async function listTestRuns() {
  const res = await apiFetch(`${getApiBase()}/tests/runs`, { headers: buildHeaders() });
  return handleResponse(res) as Promise<{ items: TestRunDetail[] }>;
}

export async function getTestRun(runId: string) {
  const res = await apiFetch(`${getApiBase()}/tests/runs/${runId}`, { headers: buildHeaders() });
  return handleResponse(res) as Promise<TestRunDetail>;
}
