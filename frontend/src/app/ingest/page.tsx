"use client";

import { useState } from "react";
import { uploadFile } from "@/lib/api";

type UploadResult = {
  job_id: string;
  status: string;
  imported_rows?: number;
  skipped_rows?: number;
  report?: { issues?: unknown[] };
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
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleUpload(endpoint: string, file: File) {
    setLoading(true);
    setError("");
    try {
      const res = await uploadFile(endpoint, file);
      setResult(res);
    } catch (err) {
      setError(String(err).replace(/^Error:\s*/, ""));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">データ取り込み</h1>
        <p className="mt-2 text-slate-400">
          Excel / 日報 / PDF をアップロードして DB 化します。まずは下のサンプルをダウンロードして試せます。
        </p>
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h2 className="font-semibold text-emerald-400">サンプルデータ</h2>
        <p className="mt-1 text-sm text-slate-400">
          ダウンロード後、下の各カードへアップロードしてください（要ログイン）。
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
              disabled={loading}
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
        </div>
      )}
    </div>
  );
}
