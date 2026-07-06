"use client";

import { useEffect, useState } from "react";

type BackendStatus = {
  configured: boolean;
  backend_url: string | null;
  on_railway: boolean;
  hint: string | null;
};

export function BackendStatusBanner() {
  const [status, setStatus] = useState<BackendStatus | null>(null);

  useEffect(() => {
    fetch("/api/backend-status")
      .then((res) => res.json())
      .then(setStatus)
      .catch(() => null);
  }, []);

  if (!status || status.configured) return null;

  return (
    <div className="mb-6 rounded-xl border border-amber-700/50 bg-amber-950/30 p-4 text-amber-100">
      <p className="font-medium">Backend API が未接続です</p>
      <p className="mt-2 text-sm text-amber-200/80">
        {status.hint ||
          "最新コードを再デプロイしてください。Dockerfile.combined で UI と API が同一コンテナで起動します。"}
      </p>
      {status.on_railway && (
        <ul className="mt-3 list-inside list-disc space-y-1 text-xs text-amber-300/80">
          <li>Root Directory: <code className="text-amber-200">frontend</code> のままで OK</li>
          <li>PostgreSQL プラグインをリンクし <code className="text-amber-200">DATABASE_URL</code> を設定</li>
          <li>再デプロイ後 <code className="text-amber-200">/api/backend-status</code> が configured: true になること</li>
        </ul>
      )}
    </div>
  );
}
