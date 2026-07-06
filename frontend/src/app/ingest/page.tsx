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
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">データ取り込み</h1>
      <p className="text-slate-400">Excel / 日報 / PDF をアップロードして DB 化します。</p>

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
