"use client";

import { useState } from "react";
import { runEval } from "@/lib/api";

export default function EvalPage() {
  const [metrics, setMetrics] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleRun() {
    setLoading(true);
    setError("");
    try {
      const res = await runEval();
      setMetrics(res.metrics);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">回答精度評価</h1>
      <p className="text-slate-400">
        ゴールド Q&A セットに対して Retrieval / 引用 / キーワードカバレッジを計測します。
      </p>

      <button
        onClick={handleRun}
        disabled={loading}
        className="rounded-lg bg-emerald-600 px-6 py-2 font-medium hover:bg-emerald-500 disabled:opacity-50"
      >
        {loading ? "評価中..." : "評価を実行"}
      </button>

      {error && <p className="text-red-400">{error}</p>}

      {metrics && (
        <div className="grid gap-4 md:grid-cols-2">
          {Object.entries(metrics).map(([key, value]) => (
            <div key={key} className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <p className="text-sm text-slate-400">{key}</p>
              <p className="mt-1 text-2xl font-bold text-emerald-400">
                {typeof value === "number" && value <= 1
                  ? `${(value * 100).toFixed(1)}%`
                  : value}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
