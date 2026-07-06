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
          "Frontend の環境変数 BACKEND_URL に Backend サービスの公開 URL を設定し、再デプロイしてください。"}
      </p>
      {status.on_railway && (
        <p className="mt-2 font-mono text-xs text-amber-300/70">
          例: BACKEND_URL=https://&lt;backend-service&gt;.up.railway.app
        </p>
      )}
    </div>
  );
}
