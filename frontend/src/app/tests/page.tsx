"use client";

import { useCallback, useEffect, useState } from "react";
import { getTestRun, listTestRuns, runTests, type TestRunDetail, type TestSuite } from "@/lib/api";

function outcomeColor(outcome: string) {
  if (outcome === "passed") return "text-emerald-400";
  if (outcome === "failed") return "text-red-400";
  return "text-amber-400";
}

function statusBadge(status: string) {
  const base = "rounded-full px-3 py-1 text-xs font-medium";
  if (status === "passed") return `${base} bg-emerald-950 text-emerald-400 border border-emerald-800`;
  return `${base} bg-red-950 text-red-400 border border-red-800`;
}

export default function TestsPage() {
  const [suite, setSuite] = useState<TestSuite>("unit");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<TestRunDetail | null>(null);
  const [history, setHistory] = useState<TestRunDetail[]>([]);

  const loadHistory = useCallback(async () => {
    try {
      const res = await listTestRuns();
      setHistory(res.items);
    } catch {
      // 認証前などは無視
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  async function handleRun() {
    setLoading(true);
    setError("");
    try {
      const res = await runTests(suite);
      setResult(res);
      await loadHistory();
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectRun(runId: string) {
    setError("");
    try {
      const res = await getTestRun(runId);
      setResult(res);
    } catch (err) {
      setError(String(err));
    }
  }

  const summary = result?.summary;

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-bold">テスト実行</h1>
        <p className="mt-2 text-slate-400">
          pytest テストクラスを実行し、結果をブラウザで確認できます。
        </p>
      </section>

      <section className="flex flex-wrap items-end gap-4">
        <div>
          <label className="mb-1 block text-sm text-slate-400">スイート</label>
          <select
            value={suite}
            onChange={(e) => setSuite(e.target.value as TestSuite)}
            className="rounded-lg border border-slate-700 bg-slate-900 px-4 py-2"
          >
            <option value="unit">Unit（DB 不要）</option>
            <option value="integration">Integration（DB 必要）</option>
            <option value="all">All</option>
          </select>
        </div>
        <button
          onClick={handleRun}
          disabled={loading}
          className="rounded-lg bg-emerald-600 px-6 py-2 font-medium hover:bg-emerald-500 disabled:opacity-50"
        >
          {loading ? "実行中..." : "テストを実行"}
        </button>
      </section>

      {error && (
        <div className="rounded-lg border border-red-900/50 bg-red-950/30 p-4 text-red-300">
          <p>{error}</p>
          <p className="mt-2 text-sm text-slate-400">
            Railway Frontend に <code className="text-red-200">BACKEND_URL</code>（Backend の公開 URL）が未設定の可能性があります。
          </p>
        </div>
      )}

      {summary && result && (
        <section className="space-y-6">
          <div className="flex flex-wrap items-center gap-3">
            <span className={statusBadge(result.status)}>{result.status.toUpperCase()}</span>
            <span className="text-sm text-slate-400">suite: {result.suite}</span>
            <span className="text-sm text-slate-400">{result.duration_sec}s</span>
          </div>

          <div className="grid gap-4 md:grid-cols-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <p className="text-sm text-slate-400">Total</p>
              <p className="mt-1 text-2xl font-bold">{summary.total}</p>
            </div>
            <div className="rounded-xl border border-emerald-900/50 bg-emerald-950/20 p-4">
              <p className="text-sm text-slate-400">Passed</p>
              <p className="mt-1 text-2xl font-bold text-emerald-400">{summary.passed}</p>
            </div>
            <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-4">
              <p className="text-sm text-slate-400">Failed</p>
              <p className="mt-1 text-2xl font-bold text-red-400">{summary.failed}</p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <p className="text-sm text-slate-400">Skipped</p>
              <p className="mt-1 text-2xl font-bold text-amber-400">{summary.skipped}</p>
            </div>
          </div>

          <div className="space-y-4">
            <h2 className="font-semibold">テストクラス別結果</h2>
            {(result.classes ?? []).map((cls) => (
              <div key={`${cls.module}-${cls.class_name}`} className="rounded-xl border border-slate-800 bg-slate-900">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 px-4 py-3">
                  <div>
                    <p className="font-medium">{cls.class_name}</p>
                    <p className="text-xs text-slate-500">{cls.module}</p>
                  </div>
                  <p className="text-sm text-slate-400">
                    {cls.passed}/{cls.total} passed
                  </p>
                </div>
                <ul className="divide-y divide-slate-800">
                  {cls.tests.map((test) => (
                    <li key={test.name} className="px-4 py-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-mono text-sm">{test.name}</span>
                        <span className={`text-sm font-medium ${outcomeColor(test.outcome)}`}>
                          {test.outcome}
                        </span>
                      </div>
                      {test.message && (
                        <pre className="mt-2 overflow-x-auto rounded bg-slate-950 p-3 text-xs text-red-300">
                          {test.message}
                        </pre>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {history.length > 0 && (
        <section className="space-y-3">
          <h2 className="font-semibold">実行履歴</h2>
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="w-full text-sm">
              <thead className="bg-slate-900 text-slate-400">
                <tr>
                  <th className="px-4 py-2 text-left">日時</th>
                  <th className="px-4 py-2 text-left">Suite</th>
                  <th className="px-4 py-2 text-left">Status</th>
                  <th className="px-4 py-2 text-left">Passed</th>
                  <th className="px-4 py-2 text-left">Failed</th>
                  <th className="px-4 py-2 text-left"></th>
                </tr>
              </thead>
              <tbody>
                {history.map((run) => (
                  <tr key={run.run_id} className="border-t border-slate-800">
                    <td className="px-4 py-2">{new Date(run.created_at).toLocaleString("ja-JP")}</td>
                    <td className="px-4 py-2">{run.suite}</td>
                    <td className={`px-4 py-2 ${outcomeColor(run.status === "passed" ? "passed" : "failed")}`}>
                      {run.status}
                    </td>
                    <td className="px-4 py-2">{run.summary.passed}</td>
                    <td className="px-4 py-2">{run.summary.failed}</td>
                    <td className="px-4 py-2">
                      <button
                        onClick={() => handleSelectRun(run.run_id)}
                        className="text-emerald-400 hover:underline"
                      >
                        詳細
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
