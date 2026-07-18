"use client";

import { useState } from "react";
import { runEval } from "@/lib/api";

type EvalMetrics = {
  retrieval_hit_at_3?: number | null;
  retrieval_hit_at_5?: number | null;
  citation_accuracy?: number | null;
  keyword_coverage_avg?: number | null;
  total_cases?: number;
  scored_retrieval_cases?: number;
  failed_cases?: number;
};

type CaseResult = {
  case_id?: string;
  question?: string;
  hit_at_3?: boolean;
  hit_at_5?: boolean;
  citation_match?: boolean;
  keyword_coverage?: number;
  expected_resolved?: boolean;
  top_equipment?: string | null;
  error?: string;
};

type MetricCard = {
  key: keyof EvalMetrics;
  label: string;
  meaning: string;
  howToImprove: string;
  format: "percent" | "count";
};

const METRIC_CARDS: MetricCard[] = [
  {
    key: "retrieval_hit_at_3",
    label: "検索ヒット率（上位3件）",
    meaning:
      "正解の保全実績が、検索結果の上位3件に含まれた割合です。高いほど「正しい過去事例を見つけられている」状態です。",
    howToImprove:
      "設備名・症状を質問に含める、データを再取り込み（マルチチャンク）、RETRIEVAL_TOP_K を上げる。",
    format: "percent",
  },
  {
    key: "retrieval_hit_at_5",
    label: "検索ヒット率（上位5件）",
    meaning:
      "正解実績が上位5件に含まれた割合です。Hit@3 より条件が緩い指標で、拾い漏れの有無を見ます。",
    howToImprove: "キーワード検索・再ランクの改善、ゴールドの expected_match_terms を見直す。",
    format: "percent",
  },
  {
    key: "citation_accuracy",
    label: "引用一致率",
    meaning:
      "回答の根拠として使う上位検索結果に、正解実績が含まれた割合です。検索と引用の整合性を表します。",
    howToImprove: "関連度順コンテキストを維持し、誤った設備の実績が上位に来ないよう再ランクを調整。",
    format: "percent",
  },
  {
    key: "keyword_coverage_avg",
    label: "キーワード含有率",
    meaning:
      "生成された回答に、期待キーワード（例: ベアリング、異音）がどれだけ含まれたかの平均です。回答内容の妥当性を見ます。",
    howToImprove: "プロンプトで根拠キーワードを明示させる、正解実績が上位に来るよう検索を改善。",
    format: "percent",
  },
  {
    key: "total_cases",
    label: "評価ケース数",
    meaning: "今回実行したゴールド Q&A の件数です（data/eval/gold_qa.json）。",
    howToImprove: "ケースを増やして回帰監視を強化する。",
    format: "count",
  },
  {
    key: "scored_retrieval_cases",
    label: "検索評価対象数",
    meaning:
      "正解レコードを DB から解決できたケース数です。0 のときは検索ヒット率が計算できません。",
    howToImprove: "サンプルデータを seed / 取り込みし、設備名がゴールドと一致しているか確認。",
    format: "count",
  },
  {
    key: "failed_cases",
    label: "失敗ケース数",
    meaning: "評価中に例外で落ちたケース数です。0 が正常です。",
    howToImprove: "エラー内容を確認し、Backend ログや OpenAI / DB 接続を点検。",
    format: "count",
  },
];

function formatMetric(value: number | null | undefined, format: "percent" | "count"): string {
  if (value === null || value === undefined) return "—";
  if (format === "percent") return `${(value * 100).toFixed(1)}%`;
  return String(value);
}

function metricTone(key: keyof EvalMetrics, value: number | null | undefined): string {
  if (value === null || value === undefined) return "text-slate-400";
  if (key === "failed_cases") return value === 0 ? "text-emerald-400" : "text-red-400";
  if (key === "total_cases" || key === "scored_retrieval_cases") return "text-emerald-400";
  if (value >= 0.8) return "text-emerald-400";
  if (value >= 0.5) return "text-amber-300";
  return "text-red-400";
}

export default function EvalPage() {
  const [metrics, setMetrics] = useState<EvalMetrics | null>(null);
  const [cases, setCases] = useState<CaseResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleRun() {
    setLoading(true);
    setError("");
    try {
      const res = (await runEval()) as {
        metrics: EvalMetrics;
        case_results?: { cases?: CaseResult[] };
      };
      setMetrics(res.metrics);
      setCases(res.case_results?.cases ?? []);
    } catch (err) {
      setError(String(err).replace(/^Error:\s*/, ""));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div className="space-y-3">
        <h1 className="text-2xl font-bold">回答精度評価</h1>
        <p className="max-w-3xl text-slate-400">
          ゴールド Q&A に対して「正しい過去実績を探せたか」「回答に重要語が入っているか」を測ります。
          数値は高いほど良いです（失敗ケース数のみ低いほど良い）。
        </p>
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-300">
          <p className="font-medium text-slate-200">見方のポイント</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-slate-400">
            <li>
              <span className="text-slate-200">検索ヒット率</span> — 正しい実績を上位に出せているか
            </li>
            <li>
              <span className="text-slate-200">引用一致率</span> — 回答根拠が正解実績と一致しているか
            </li>
            <li>
              <span className="text-slate-200">キーワード含有率</span> — 回答文に期待語（原因・症状など）が入っているか
            </li>
            <li>
              以前 0% だった場合 — 正解 ID 未設定が原因でした。現在は設備名+用語で DB から自動解決します
            </li>
          </ul>
        </div>
      </div>

      <button
        onClick={handleRun}
        disabled={loading}
        className="rounded-lg bg-emerald-600 px-6 py-2 font-medium hover:bg-emerald-500 disabled:opacity-50"
      >
        {loading ? "評価中...（数十秒〜数分）" : "評価を実行"}
      </button>

      {error && <p className="text-red-400">{error}</p>}

      {metrics && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">総合指標</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {METRIC_CARDS.map((card) => {
              const value = metrics[card.key];
              return (
                <div
                  key={card.key}
                  className="rounded-xl border border-slate-800 bg-slate-900 p-4"
                >
                  <p className="text-sm text-slate-300">{card.label}</p>
                  <p className={`mt-1 text-2xl font-bold ${metricTone(card.key, value as number | null)}`}>
                    {formatMetric(value as number | null | undefined, card.format)}
                  </p>
                  <p className="mt-3 text-xs leading-relaxed text-slate-500">{card.meaning}</p>
                  <p className="mt-2 text-xs leading-relaxed text-slate-400">
                    <span className="text-slate-300">改善ヒント: </span>
                    {card.howToImprove}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {cases.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">ケース別結果</h2>
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-900 text-slate-400">
                <tr>
                  <th className="px-3 py-2 whitespace-nowrap">ID</th>
                  <th className="px-3 py-2">質問</th>
                  <th className="px-3 py-2 whitespace-nowrap">Hit@3</th>
                  <th className="px-3 py-2 whitespace-nowrap">Hit@5</th>
                  <th className="px-3 py-2 whitespace-nowrap">引用</th>
                  <th className="px-3 py-2 whitespace-nowrap">キーワード</th>
                  <th className="px-3 py-2 whitespace-nowrap">トップ設備</th>
                </tr>
              </thead>
              <tbody>
                {cases.map((c) => (
                  <tr key={c.case_id} className="border-t border-slate-800">
                    <td className="px-3 py-2 whitespace-nowrap text-slate-300">{c.case_id}</td>
                    <td className="px-3 py-2 text-slate-300">{c.question ?? c.error ?? "—"}</td>
                    <td className="px-3 py-2">{c.error ? "—" : c.hit_at_3 ? "○" : "×"}</td>
                    <td className="px-3 py-2">{c.error ? "—" : c.hit_at_5 ? "○" : "×"}</td>
                    <td className="px-3 py-2">{c.error ? "—" : c.citation_match ? "○" : "×"}</td>
                    <td className="px-3 py-2">
                      {typeof c.keyword_coverage === "number"
                        ? `${(c.keyword_coverage * 100).toFixed(0)}%`
                        : "—"}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-emerald-400">
                      {c.top_equipment ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
