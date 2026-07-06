"use client";

import { useCallback, useEffect, useState } from "react";
import { getStats, listRecords, seedDatabase } from "@/lib/api";
import { RecordTable } from "@/components/RecordTable";
import type { MaintenanceRecord } from "@/lib/records";

export default function RecordsPage() {
  const [records, setRecords] = useState<MaintenanceRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listRecords(filter || undefined);
      setRecords(res.items);
      setTotal(res.total);
      const stats = await getStats();
      setTotal(stats.total_records);
    } catch (err) {
      setMessage(`読み込みエラー: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSeed() {
    setSeeding(true);
    setMessage("");
    try {
      const res = await seedDatabase();
      setMessage(`テストデータ投入完了（合計 ${res.total_records} 件）`);
      await load();
    } catch (err) {
      setMessage(`投入エラー: ${err}`);
    } finally {
      setSeeding(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">保全実績一覧</h1>
          <p className="mt-1 text-slate-400">PostgreSQL に登録されたテストデータ（全 {total} 件）</p>
        </div>
        <button
          onClick={handleSeed}
          disabled={seeding}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
        >
          {seeding ? "投入中..." : "テストデータ再投入"}
        </button>
      </div>

      <div className="flex gap-3">
        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="設備名でフィルタ（例: コンプレッサA-03）"
          className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-sm"
        />
        <button
          onClick={load}
          className="rounded-lg border border-slate-700 px-4 py-2 text-sm hover:border-emerald-700"
        >
          検索
        </button>
      </div>

      {message && <p className="text-sm text-emerald-400">{message}</p>}
      {loading ? (
        <p className="text-slate-400">読み込み中...</p>
      ) : (
        <RecordTable records={records} />
      )}
    </div>
  );
}
