"use client";

import { useEffect, useState } from "react";

type BackendStatus = {
  configured: boolean;
  backend_url: string | null;
  on_railway: boolean;
  combined_deploy?: boolean;
  node_env?: string | null;
  deployed_commit?: string | null;
  hint: string | null;
};

export function BackendStatusBanner() {
  const [status, setStatus] = useState<BackendStatus | null>(null);
  const [proxyOk, setProxyOk] = useState<boolean | null>(null);

  useEffect(() => {
    fetch("/api/backend-status")
      .then((res) => res.json())
      .then(setStatus)
      .catch(() => null);

    fetch("/backend/health")
      .then((res) => setProxyOk(res.ok))
      .catch(() => setProxyOk(false));
  }, []);

  if (!status) return null;

  const badDeploy =
    status.on_railway &&
    (status.node_env !== "production" || status.combined_deploy !== true || proxyOk === false);

  if (status.configured && !badDeploy) return null;

  return (
    <div className="mb-6 rounded-xl border border-amber-700/50 bg-amber-950/30 p-4 text-amber-100">
      <p className="font-medium">
        {status.configured ? "Backend API プロキシが動作していません" : "Backend API が未接続です"}
      </p>
      <p className="mt-2 text-sm text-amber-200/80">
        {status.hint ||
          "Railway で Dockerfile.railway（UI+API 一体）をビルドし、キャッシュをクリアして再デプロイしてください。"}
      </p>
      {status.on_railway && (
        <ul className="mt-3 list-inside list-disc space-y-1 text-xs text-amber-300/80">
          <li>Builder: Dockerfile / Dockerfile path: <code className="text-amber-200">Dockerfile.railway</code></li>
          <li>Start Command は空（または <code className="text-amber-200">/start.sh</code>）— <code className="text-amber-200">npm run dev</code> 禁止</li>
          <li><code className="text-amber-200">BACKEND_URL</code> に本番 URL を設定しない</li>
          <li>再デプロイ後 <code className="text-amber-200">/backend/health</code> が JSON を返すこと</li>
          {status.node_env && (
            <li>現在: node_env={status.node_env}, combined={String(status.combined_deploy)}</li>
          )}
        </ul>
      )}
    </div>
  );
}
