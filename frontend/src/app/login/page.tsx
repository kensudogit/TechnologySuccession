"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { getAuthStatus, login } from "@/lib/api";
import { clearToken, isLoggedIn, setToken } from "@/lib/auth";

const DEFAULT_USERNAME = "admin";
const DEFAULT_PASSWORD = "admin";

export default function LoginPage() {
  const router = useRouter();
  const passwordRef = useRef<HTMLInputElement>(null);
  const [username, setUsername] = useState(DEFAULT_USERNAME);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [authEnabled, setAuthEnabled] = useState<boolean | null>(null);

  useEffect(() => {
    if (isLoggedIn()) {
      router.replace("/");
      return;
    }

    getAuthStatus()
      .then((s) => {
        setAuthEnabled(s.auth_enabled);
        if (!s.auth_enabled) router.replace("/");
      })
      .catch(() => setAuthEnabled(false));
  }, [router]);

  useEffect(() => {
    if (authEnabled) {
      passwordRef.current?.focus();
    }
  }, [authEnabled]);

  function fillDefaultCredentials() {
    setUsername(DEFAULT_USERNAME);
    setPassword(DEFAULT_PASSWORD);
    setError("");
    passwordRef.current?.focus();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!password.trim()) {
      setError("パスワードを入力してください（未変更時は admin）。");
      passwordRef.current?.focus();
      return;
    }
    setLoading(true);
    setError("");
    clearToken();
    try {
      const res = await login(username, password);
      setToken(res.access_token);
      router.push("/");
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message.replace(/^Error:\s*/, ""));
    } finally {
      setLoading(false);
    }
  }

  if (authEnabled === null) {
    return <p className="text-slate-400">読み込み中...</p>;
  }

  if (!authEnabled) {
    return <p className="text-slate-400">認証は無効です（JWT_SECRET 未設定）</p>;
  }

  return (
    <div className="mx-auto max-w-md space-y-6">
      <div>
        <h1 className="text-2xl font-bold">ログイン</h1>
        <p className="mt-2 text-sm text-slate-400">
          Chat・Tests・Ingest など保護 API へアクセスするにはログインが必要です。
        </p>
        <p className="mt-2 rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm text-slate-300">
          初期値: <code className="text-emerald-300">admin</code> /{" "}
          <code className="text-emerald-300">admin</code>
          <br />
          Railway で <code className="text-slate-200">AUTH_PASSWORD</code> を変更している場合はその値を入力してください。
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-6">
        <div>
          <label className="mb-1 block text-sm text-slate-400">ユーザー名</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2"
            autoComplete="username"
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-slate-400">パスワード</label>
          <input
            ref={passwordRef}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="admin（デフォルト）"
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-2"
            autoComplete="current-password"
            required
          />
        </div>

        <button
          type="button"
          onClick={fillDefaultCredentials}
          className="w-full rounded-lg border border-slate-700 py-2 text-sm text-slate-300 hover:border-slate-500 hover:text-slate-100"
        >
          デフォルト（admin / admin）を入力
        </button>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-emerald-600 py-2 font-medium hover:bg-emerald-500 disabled:opacity-50"
        >
          {loading ? "ログイン中..." : "ログイン"}
        </button>
      </form>
    </div>
  );
}
