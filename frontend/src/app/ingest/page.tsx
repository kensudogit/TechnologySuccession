"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { seedDatabase, uploadFile } from "@/lib/api";

type UploadResult = {
  job_id: string;
  status: string;
  imported_rows?: number;
  skipped_rows?: number;
  report?: { issues?: unknown[] };
};

type SeedResult = {
  excel_imported?: number;
  excel_skipped?: number;
  daily_imported?: number;
  daily_skipped?: number;
  total_records?: number;
};

const SAMPLE_FILES = [
  {
    label: "Excel 保全実績（12件）",
    href: "/samples/maintenance_records_sample.xlsx",
    filename: "maintenance_records_sample.xlsx",
    hint: "点検日・設備名・異常・原因・処置など",
  },
  {
    label: "日報テキスト（8件）",
    href: "/samples/daily_report_sample.txt",
    filename: "daily_report_sample.txt",
    hint: "日付 / 設備 / 異常 / 処置ブロック",
  },
  {
    label: "保全マニュアル PDF",
    href: "/samples/maintenance_manual_sample.pdf",
    filename: "maintenance_manual_sample.pdf",
    hint: "異音・圧力低下・過電流の標準対応",
  },
] as const;

export default function IngestPage() {
  const router = useRouter();
  const [result, setResult] = useState<UploadResult | null>(null);
  const [seedResult, setSeedResult] = useState<SeedResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);

  async function handleUpload(endpoint: string, file: File) {
    setLoading(true);
    setError("");
    setSeedResult(null);
    try {
      const res = await uploadFile(endpoint, file);
      setResult(res);
    } catch (err) {
      setError(String(err).replace(/^Error:\s*/, ""));
    } finally {
      setLoading(false);
    }
  }

  async function handleSeedToPostgres() {
    setSeeding(true);
    setError("");
    setResult(null);
    try {
      const res = (await seedDatabase()) as SeedResult;
      setSeedResult(res);
      // 一覧画面へ遷移して PostgreSQL の内容を表示
      router.push("/records");
    } catch (err) {
      setError(String(err).replace(/^Error:\s*/, ""));
    } finally {
      setSeeding(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">データ取り込み</h1>
        <p className="mt-2 text-slate-400">
          サンプルを PostgreSQL に登録するか、ファイルをアップロードして DB 化します。
        </p>
      </div>

      <section className="rounded-xl border border-emerald-900/40 bg-emerald-950/20 p-5">
        <h2 className="font-semibold text-emerald-400">かんたん登録（推奨）</h2>
        <p className="mt-2 text-sm text-slate-300">
          サンプル Excel（12件）と日報を PostgreSQL に投入し、保全実績一覧へ表示します。
          既に同じ内容がある行は重複スキップされます。
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleSeedToPostgres}
            disabled={seeding || loading}
            className="rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
          >
            {seeding ? "PostgreSQL に登録中..." : "サンプルを PostgreSQL に登録して一覧へ"}
          </button>
          <Link
            href="/records"
            className="rounded-lg border border-slate-700 px-5 py-2.5 text-sm text-slate-300 hover:border-emerald-700"
          >
            保全実績一覧を見る
          </Link>
        </div>
        {seedResult && (
          <p className="mt-3 text-sm text-emerald-300">
            登録完了 — Excel +{seedResult.excel_imported ?? 0} / 日報 +
            {seedResult.daily_imported ?? 0} / 合計 {seedResult.total_records ?? 0} 件
          </p>
        )}
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h2 className="font-semibold text-slate-200">サンプルファイル（手動アップロード用）</h2>
        <p className="mt-1 text-sm text-slate-400">
          ダウンロード後、下の各カードへアップロードすることもできます。
        </p>
        <ul className="mt-4 space-y-3">
          {SAMPLE_FILES.map((sample) => (
            <li
              key={sample.href}
              className="flex flex-col gap-1 rounded-lg border border-slate-800 bg-slate-950/50 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <p className="font-medium text-slate-200">{sample.label}</p>
                <p className="text-xs text-slate-500">{sample.hint}</p>
              </div>
              <a
                href={sample.href}
                download={sample.filename}
                className="text-sm text-emerald-400 hover:underline"
              >
                ダウンロード
              </a>
            </li>
          ))}
        </ul>
      </section>

      <div className="grid gap-4 md:grid-cols-3">
        {[
          { label: "Excel 保全実績", endpoint: "/ingest/excel", accept: ".xlsx,.xls" },
          { label: "日報 (txt)", endpoint: "/ingest/daily-report", accept: ".txt" },
          { label: "PDF / 画像", endpoint: "/ingest/document", accept: ".pdf,.jpg,.jpeg,.png" },
        ].map((item) => (
          <label
            key={item.endpoint}
            className="flex cursor-pointer flex-col items-center rounded-xl border border-dashed border-slate-700 bg-slate-900 p-6 hover:border-emerald-700"
          >
            <span className="font-medium">{item.label}</span>
            <span className="mt-2 text-xs text-slate-500">{item.accept}</span>
            <input
              type="file"
              accept={item.accept}
              className="hidden"
              disabled={loading || seeding}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleUpload(item.endpoint, file);
              }}
            />
          </label>
        ))}
      </div>

      {loading && <p className="text-emerald-400">取り込み中...</p>}
      {error && <p className="text-red-400">{error}</p>}

      {result && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="font-semibold">取り込み結果</h2>
          <dl className="mt-4 grid grid-cols-2 gap-2 text-sm">
            <dt className="text-slate-400">Job ID</dt>
            <dd>{result.job_id}</dd>
            <dt className="text-slate-400">Status</dt>
            <dd>{result.status}</dd>
            <dt className="text-slate-400">Imported</dt>
            <dd>{result.imported_rows ?? 0}</dd>
            <dt className="text-slate-400">Skipped</dt>
            <dd>{result.skipped_rows ?? 0}</dd>
          </dl>
          <Link href="/records" className="mt-4 inline-block text-sm text-emerald-400 hover:underline">
            保全実績一覧で確認する →
          </Link>
        </div>
      )}
    </div>
  );
}
