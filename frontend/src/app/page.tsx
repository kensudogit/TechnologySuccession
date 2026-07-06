"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getStats, listRecords, getAuthStatus } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";
import { RecordTable } from "@/components/RecordTable";
import type { MaintenanceRecord } from "@/lib/records";

export default function DashboardPage() {
  const [stats, setStats] = useState<{ total_records: number } | null>(null);
  const [records, setRecords] = useState<MaintenanceRecord[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const auth = await getAuthStatus();
        if (auth.auth_enabled && !isLoggedIn()) return;

        const [statsRes, recordsRes] = await Promise.all([getStats(), listRecords()]);
        setStats(statsRes);
        setRecords(recordsRes.items.slice(0, 5));
        setError("");
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setError(message.replace(/^Error:\s*/, ""));
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-bold">保全実績 RAG システム</h1>
        <p className="mt-2 text-slate-400">
          数年分の保全実績を検索し、現場トラブルシューティングを支援します。
        </p>
      </section>

      {error && (
        <div className="rounded-lg border border-red-900 bg-red-950/50 p-4 text-sm text-red-300">
          <p>API接続エラー: {error}</p>
          {error.includes("認証が必要") && (
            <Link href="/login" className="mt-2 inline-block text-emerald-400 hover:underline">
              ログインページへ →
            </Link>
          )}
          {error.includes("Backend API") && (
            <button
              type="button"
              className="mt-2 block text-emerald-400 hover:underline"
              onClick={() => window.location.reload()}
            >
              ページを再読み込み
            </button>
          )}
        </div>
      )}

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <p className="text-sm text-slate-400">登録実績件数</p>
          <p className="mt-2 text-3xl font-bold text-emerald-400">
            {stats?.total_records ?? "—"}
          </p>
        </div>
        <Link
          href="/chat"
          className="rounded-xl border border-emerald-900/50 bg-emerald-950/30 p-6 hover:border-emerald-700"
        >
          <p className="font-semibold">トラブルシューティング</p>
          <p className="mt-2 text-sm text-slate-400">過去実績から原因・処置を検索</p>
        </Link>
        <Link
          href="/records"
          className="rounded-xl border border-slate-800 bg-slate-900 p-6 hover:border-slate-600"
        >
          <p className="font-semibold">保全実績一覧</p>
          <p className="mt-2 text-sm text-slate-400">PostgreSQL のデータを表示</p>
        </Link>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">最近の保全実績</h2>
          <Link href="/records" className="text-sm text-emerald-400 hover:underline">
            すべて見る →
          </Link>
        </div>
        <RecordTable records={records} compact />
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <h2 className="font-semibold">クイック質問例</h2>
        <ul className="mt-4 space-y-2 text-sm text-slate-300">
          <li>• コンプレッサA-03の異音、過去の原因は？</li>
          <li>• ポンプB-12の圧力低下、前回の処置は？</li>
          <li>• モータC-01の過電流、過去事例は？</li>
        </ul>
      </section>
    </div>
  );
}
