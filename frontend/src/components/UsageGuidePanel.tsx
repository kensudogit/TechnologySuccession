"use client";

/**
 * 画面右下のドラッグ可能な利用手順パネル（localStorage で位置・開閉を保存）。
 */
import { useCallback, useEffect, useRef, useState } from "react";

const STORAGE_KEY = "ts-rag-usage-guide-v1";
const PANEL_WIDTH = 440;

type GuideStep = {
  title: string;
  body: string;
  items?: readonly string[];
};

type FeaturedBlock = {
  badge: string;
  title: string;
  body: string;
  items?: readonly string[];
  variant?: "architecture" | "rag" | "ingest" | "chat" | "auth" | "eval" | "default";
};

const architectureFeatured: FeaturedBlock = {
  badge: "Architecture",
  title: "Next.js BFF + FastAPI 一体デプロイ",
  body:
    "Railway 上で Next.js（PORT）と FastAPI（内部 :18080）を同一コンテナで起動。ブラウザは /api/backend/* 経由で API に接続し、127.0.0.1 への直接アクセスは不要です。",
  variant: "architecture",
  items: [
    "Next.js — UI · /api/backend プロキシ · server.js",
    "FastAPI :18080 — RAG · 取り込み · 認証 · テスト実行",
    "PostgreSQL + pgvector — 保全実績 · チャンク Embedding · FTS",
    "LangChain — OpenAIEmbeddings · ChatOpenAI · Prompt チェーン",
    "LlamaIndex — Document · Vector/Keyword Retriever · RRF + 再ランク",
    "/api/backend-status — デプロイ診断 · /health — 生存確認",
  ],
};

const ragFeatured: FeaturedBlock = {
  badge: "RAG",
  title: "LangChain + LlamaIndex ハイブリッド検索",
  body:
    "クエリ書き換え後に pgvector / キーワード検索し、RRF 融合と設備・症状ブーストで再ランク。関連度順コンテキストを LangChain GPT-4o で回答します。",
  variant: "rag",
  items: [
    "クエリ理解 — 設備名・症状・別名を Embedding / キーワードに反映",
    "取り込み — summary / 症状 / 原因 / 処置のマルチチャンク + バッチ Embedding",
    "ベクトル検索 — MaintenanceVectorRetriever（コサイン類似度）",
    "キーワード検索 — 日本語 ILIKE OR + 設備ブースト（ハードフィルタなし）",
    "融合・再ランク — Sequential RRF → 設備/症状ブーストで並べ替え",
    "生成 — 意図別プロンプト + LangChain ChatOpenAI",
    "信頼度 — vector score 基準（high ≥0.55 / medium ≥0.35）",
    "GET /api/backend/rag/status — フレームワーク構成の確認",
  ],
};

const evalFeatured: FeaturedBlock = {
  badge: "Eval",
  title: "RAG 精度評価（/eval）",
  body:
    "ゴールド Q&A に対し、検索ヒット率・引用一致率・キーワード含有率を計測します。画面上に各指標の意味と改善ヒントを表示します。",
  variant: "eval",
  items: [
    "検索ヒット率（上位3/5件）— 正解実績を上位に出せたか（高いほど良い）",
    "引用一致率 — 回答根拠が正解実績と一致したか",
    "キーワード含有率 — 回答に期待語（ベアリング等）が入ったか",
    "正解解決 — 設備名 + match_terms で DB から動的に正解レコードを特定",
    "評価実行 — POST /eval/run（数十秒〜数分）",
    "オフライン評価 — backend/scripts/offline_rag_eval.py",
  ],
};

const chatFeatured: FeaturedBlock = {
  badge: "Chat",
  title: "トラブルシューティング Chat（/chat）",
  body:
    "設備名（任意）と症状・質問を入力すると、過去の保全実績を根拠に回答します。参考実績が右側に表示されます。",
  variant: "chat",
  items: [
    "設備名 — 例: コンプレッサA-03（絞り込み用・任意）",
    "質問例 —「異音が出ている。過去に似た事例は？」",
    "信頼度 — high / medium / low（ベクトル類似度から算出）",
    "回答形式 — 想定原因 · 推奨処置 · 確認ポイント · 参考実績",
    "要ログイン — JWT_SECRET 有効時は Login 後に利用",
    "OPENAI_API_KEY 未設定 — ルールベースの簡易回答にフォールバック",
  ],
};

const ingestFeatured: FeaturedBlock = {
  badge: "Ingest",
  title: "データ取り込み（/ingest）",
  body:
    "Excel・日報テキスト・PDF をアップロードすると、クレンジング → DB 保存 → Embedding 生成まで自動実行されます。",
  variant: "ingest",
  items: [
    "かんたん登録 — /ingest の「サンプルを PostgreSQL に登録して一覧へ」",
    "一覧表示 — 登録後は /records に PostgreSQL の内容を表示",
    "手動 — Excel・日報・PDF をダウンロードして各カードへアップロード",
    "API — POST /admin/seed（要ログイン）",
    "チャンク — summary + フィールド単位 + Embedding を自動生成",
    "重複排除 — content_hash で同一レコードをスキップ",
  ],
};

const authFeatured: FeaturedBlock = {
  badge: "Auth",
  title: "ログインと Railway 環境変数",
  body:
    "JWT_SECRET が設定されている場合、保護 API には Bearer トークンが必要です。",
  variant: "auth",
  items: [
    "デフォルト — admin / admin（AUTH_PASSWORD 未設定時）",
    "Login — /login → トークンを localStorage に保存",
    "Railway Variables — DATABASE_URL · JWT_SECRET · OPENAI_API_KEY",
    "AUTH_PASSWORD — 本番では必ず変更",
    "BACKEND_URL — 本番 Frontend URL を設定しない（ループ防止）",
  ],
};

const techStack = [
  "Python · FastAPI",
  "Next.js 14 · TypeScript",
  "PostgreSQL · pgvector",
  "LangChain · OpenAI",
  "LlamaIndex · RRF",
  "再ランク · マルチチャンク",
  "Docker · Railway",
  "HNSW · ILIKE",
  "pytest · Eval",
] as const;

const archDiagram = `Browser (保全担当者)
    │ HTTPS
    ▼
Next.js :PORT (Railway)
    ├─ /              ダッシュボード
    ├─ /records       保全実績一覧
    ├─ /chat          RAG チャット
    ├─ /ingest        データ取り込み
    ├─ /eval          精度評価
    ├─ /tests         pytest 実行
    ├─ /login         JWT ログイン
    └─ /api/backend/* ──proxy──► FastAPI :18080
              ├─ クエリ書き換え (設備・症状)
              ├─ pgvector (ベクトル検索)
              ├─ Keyword ILIKE + 設備ブースト
              ├─ RRF 融合 → 再ランク
              ├─ LangChain (意図別生成)
              └─ OpenAI API`;

type GuideSection = {
  label: string;
  steps: readonly GuideStep[];
};

const guideSections: readonly GuideSection[] = [
  {
    label: "クイックスタート",
    steps: [
      {
        title: "パネル操作",
        body: "本パネルは全画面で表示されます。ヘッダーをドラッグして位置を変更でき、▼▲ で折りたたみ可能です。",
        items: [
          "PC — ヘッダーをドラッグで移動 · ▼▲ で開閉",
          "表示状態 — ブラウザ localStorage に自動保存",
          "推奨フロー — Login → Records 確認 → Chat で質問 → Ingest で追加",
        ],
      },
      {
        title: "初回セットアップ（5 分）",
        body: "本番 URL またはローカルで最初に行う手順です。",
        items: [
          "① /login — admin / admin でログイン（または Railway の AUTH_PASSWORD）",
          "② / — 登録実績件数・最近の保全実績を確認",
          "③ /chat —「コンプレッサA-03の異音、過去の原因は？」で RAG を試す",
          "④ データが空 — Ingest で Excel 投入、または管理 API で seed",
          "⑤ /eval — ゴールド Q&A で精度評価（要ログイン）",
          "⑥ /tests — Unit スイートで pytest を実行（要ログイン）",
        ],
      },
      {
        title: "接続確認",
        body: "API が正常かどうかを確認するエンドポイントです。",
        items: [
          "/api/backend-status — combined_deploy · deployed_commit",
          "/api/backend/health — DB 接続 · openai · auth 状態",
          "/api/backend/rag/status — LangChain / LlamaIndex · rerank · multi_chunk",
          "/docs — Swagger API リファレンス（Backend 直接）",
        ],
      },
    ],
  },
  {
    label: "画面別ガイド",
    steps: [
      {
        title: "ダッシュボード（/）",
        body: "登録件数と最近の保全実績を一覧表示します。一覧・件数は未ログインでも閲覧可能です。",
        items: [
          "登録実績件数 — PostgreSQL の total_records",
          "最近の保全実績 — 直近 5 件",
          "クイック質問例 — Chat への導線",
        ],
      },
      {
        title: "Records（/records）",
        body: "保全実績の全件検索・フィルタ表示です。設備名・ラインは横書き（折り返しなし）で表示します。",
        items: [
          "設備名フィルタ — 部分一致検索",
          "カラム — 日付 · 設備名 · ライン · 症状 · 原因 · 処置 · 担当 · 出典",
        ],
      },
      {
        title: "Chat（/chat）",
        body: "ハイブリッド RAG で過去実績を根拠に回答します。要ログイン。",
        items: [
          "質問例 —「コンプレッサA-03の異音、過去の原因は？」",
          "処理 — クエリ書き換え → ベクトル/キーワード → RRF → 再ランク → 生成",
          "参考実績 — 関連度の高いレコードが右側に表示",
        ],
      },
      {
        title: "Eval（/eval）",
        body: "ゴールド Q&A セットで RAG 精度を評価します。各カードに指標の意味と改善ヒントがあります。要ログイン。",
        items: [
          "評価実行 — 「評価を実行」→ POST /eval/run",
          "検索ヒット率 — 正解実績が上位に入った割合（目標 80%+）",
          "キーワード含有率 — 回答に期待語が入った割合",
          "ケース別表 — 質問ごとの ○× を確認",
          "データ — data/eval/gold_qa.json（設備名+match_terms で正解解決）",
        ],
      },
      {
        title: "Tests（/tests）",
        body: "pytest をブラウザから実行し、結果をクラス別に確認します。",
        items: [
          "Unit — DB 不要（認証・クレンジング・RAG 解析等）",
          "Integration — DB 必要（要 PostgreSQL 接続）",
          "All — 全テスト実行",
          "要ログイン — 未ログイン時は Login へ誘導",
        ],
      },
    ],
  },
  {
    label: "RAG 精度評価",
    steps: [
      {
        title: "本番での評価手順",
        body: "デプロイ後に精度を確認する標準フローです。",
        items: [
          "① /login — ログイン",
          "② データ確認 — /records にサンプル実績があること",
          "③ 空または旧チャンクのみ — 管理 seed または /ingest で再投入",
          "④ /eval —「評価を実行」をクリック",
          "⑤ 指標確認 — 検索ヒット率とキーワード含有率を主に見る",
          "⑥ 低い場合 — 再シード → 再評価。画面の「改善ヒント」を参照",
        ],
      },
      {
        title: "オフライン評価（開発用）",
        body: "DB / OpenAI なしでクエリ理解と正解レコード適合を確認できます。",
        items: [
          "スクリプト — backend/scripts/offline_rag_eval.py",
          "実行例 — docker run … python scripts/offline_rag_eval.py",
          "見る指標 — Hit@1 · Hit@3 · equipment/symptom extraction · keyword coverage",
          "レポート — scripts/offline_rag_eval_report.json",
        ],
      },
      {
        title: "評価時の注意",
        body: "指標の解釈とよくある落とし穴です。",
        items: [
          "検索ヒット率 0% — データ未投入、または設備名不一致の可能性",
          "キーワード 100%・Hit 0% — 回答は良いが検索評価の正解解決ができていない",
          "ケース数 4 — 回帰監視としては少なめ。曖昧質問の追加を推奨",
          "RAG 環境変数 — RETRIEVAL_TOP_K · RRF_TOP_K · RERANK_TOP_K",
        ],
      },
    ],
  },
  {
    label: "Railway デプロイ",
    steps: [
      {
        title: "推奨設定",
        body: "Root Directory=frontend · Dockerfile.railway で UI+API 一体ビルド。",
        items: [
          "Builder — Dockerfile / Dockerfile.railway",
          "Start Command — 空（/start.sh を使用）",
          "DATABASE_URL — PostgreSQL プラグインから自動設定",
          "JWT_SECRET · OPENAI_API_KEY · ALLOWED_ORIGINS",
          "AUTH_USERNAME / AUTH_PASSWORD — 未設定時は admin / admin",
          "再デプロイ — Clear build cache 推奨",
        ],
      },
      {
        title: "よくあるエラー",
        body: "画面の赤バナーや API エラー時の確認ポイントです。",
        items: [
          "Backend API に接続できません — 再デプロイ直後は数十秒待って再読み込み",
          "認証エラー — Railway の AUTH_PASSWORD を確認（空白・引用符に注意）",
          "認証が必要 — /login から admin / admin",
          "Failed to fetch — 期限切れトークン削除 → 再ログイン",
          "評価タイムアウト — 評価は最大数分。完了まで待機",
          "npm run dev 禁止 — 本番は Docker production ビルドのみ",
        ],
      },
    ],
  },
];

const L = {
  title: "利用手順",
  subtitle: "Architecture & Ops",
  dragHint: "ドラッグで移動",
  expand: "開く",
  collapse: "閉じる",
  heroTitle: "技術継承プラットフォーム",
  heroLead:
    "製造現場の保全実績を PostgreSQL + pgvector に蓄積し、LangChain / LlamaIndex によるハイブリッド RAG でベテラン知見の継承とトラブルシューティングを支援します。",
  stackLabel: "Tech stack",
  diagramLabel: "Service topology",
  workflowLabel: "詳細利用手順",
  scrollHint: "↓ 画面別の詳細手順は下へ",
  footer: "▼▲ で開閉 · PC はヘッダーをドラッグして移動 · 表示状態は自動保存されます。",
} as const;

type SavedState = {
  x: number;
  y: number;
  expanded: boolean;
};

function defaultPosition(mobile = false) {
  if (typeof window === "undefined") return { x: 24, y: 24 };
  if (mobile || window.innerWidth < 768) {
    return { x: 8, y: Math.max(72, window.innerHeight - 72) };
  }
  const x = Math.max(16, window.innerWidth - PANEL_WIDTH - 24);
  const y = Math.max(72, window.innerHeight - 520);
  return { x, y };
}

function clampPosition(x: number, y: number, width: number, height: number) {
  const maxX = Math.max(8, window.innerWidth - width - 8);
  const maxY = Math.max(8, window.innerHeight - height - 8);
  return {
    x: Math.min(Math.max(8, x), maxX),
    y: Math.min(Math.max(8, y), maxY),
  };
}

function FeaturedSection({ block }: { block: FeaturedBlock }) {
  const variant = block.variant ?? "default";
  return (
    <section className={`usage-guide-featured usage-guide-featured--${variant}`} aria-label={block.title}>
      <div className="usage-guide-featured-head">
        <span className="usage-guide-featured-badge">{block.badge}</span>
        <strong>{block.title}</strong>
      </div>
      <p>{block.body}</p>
      {block.items?.length ? (
        <ul className="usage-guide-items">
          {block.items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

export function UsageGuidePanel() {
  const panelRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    originX: number;
    originY: number;
  } | null>(null);

  const [ready, setReady] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [pos, setPos] = useState({ x: 24, y: 24 });
  const [dragging, setDragging] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const mobile = window.innerWidth < 768;
    setIsMobile(mobile);
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as SavedState;
        setPos(mobile ? defaultPosition(true) : { x: parsed.x, y: parsed.y });
        setExpanded(mobile ? false : parsed.expanded);
      } catch {
        setPos(defaultPosition(mobile));
        if (mobile) setExpanded(false);
      }
    } else {
      setPos(defaultPosition(mobile));
      if (mobile) setExpanded(false);
    }
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    const payload: SavedState = { ...pos, expanded };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  }, [pos, expanded, ready]);

  useEffect(() => {
    if (!ready) return;
    const onResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) return;
      const el = panelRef.current;
      if (!el) return;
      setPos((current) => clampPosition(current.x, current.y, el.offsetWidth, el.offsetHeight));
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [ready]);

  const onHeaderPointerDown = useCallback(
    (e: React.PointerEvent<HTMLElement>) => {
      if (isMobile) return;
      if ((e.target as HTMLElement).closest(".usage-guide-toggle")) return;
      dragRef.current = {
        pointerId: e.pointerId,
        startX: e.clientX,
        startY: e.clientY,
        originX: pos.x,
        originY: pos.y,
      };
      setDragging(true);
      e.currentTarget.setPointerCapture(e.pointerId);
    },
    [pos.x, pos.y, isMobile]
  );

  const onHeaderPointerMove = useCallback((e: React.PointerEvent<HTMLElement>) => {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== e.pointerId) return;
    const el = panelRef.current;
    const width = el?.offsetWidth ?? PANEL_WIDTH;
    const height = el?.offsetHeight ?? 120;
    setPos(
      clampPosition(
        drag.originX + (e.clientX - drag.startX),
        drag.originY + (e.clientY - drag.startY),
        width,
        height
      )
    );
  }, []);

  const onHeaderPointerUp = useCallback((e: React.PointerEvent<HTMLElement>) => {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== e.pointerId) return;
    dragRef.current = null;
    setDragging(false);
    e.currentTarget.releasePointerCapture(e.pointerId);
  }, []);

  if (!ready) return null;

  return (
    <div
      ref={panelRef}
      className={`usage-guide-panel${expanded ? " is-expanded" : " is-collapsed"}${dragging ? " is-dragging" : ""}${isMobile ? " is-mobile" : ""}`}
      style={isMobile ? undefined : { left: pos.x, top: pos.y, width: PANEL_WIDTH }}
      role="dialog"
      aria-label={L.title}
      aria-modal="false"
    >
      <header
        className="usage-guide-header"
        onPointerDown={onHeaderPointerDown}
        onPointerMove={onHeaderPointerMove}
        onPointerUp={onHeaderPointerUp}
        onPointerCancel={onHeaderPointerUp}
      >
        <div className="usage-guide-header-text">
          <span className="usage-guide-drag-icon" aria-hidden>
            ☰
          </span>
          <div className="usage-guide-header-titles">
            <strong>{L.title}</strong>
            <span className="usage-guide-header-sub">{L.subtitle}</span>
          </div>
          <span className="usage-guide-drag-hint">{L.dragHint}</span>
        </div>
        <button
          type="button"
          className="usage-guide-toggle"
          aria-label={expanded ? L.collapse : L.expand}
          aria-expanded={expanded}
          onClick={() => setExpanded((open) => !open)}
        >
          {expanded ? "▼" : "▲"}
        </button>
      </header>

      {expanded ? (
        <div className="usage-guide-body">
          <div className="usage-guide-hero">
            <p className="usage-guide-hero-kicker">技術継承プラットフォーム</p>
            <h2 className="usage-guide-hero-title">{L.heroTitle}</h2>
            <p className="usage-guide-hero-lead">{L.heroLead}</p>
            <div className="usage-guide-stack" aria-label={L.stackLabel}>
              {techStack.map((tag) => (
                <span key={tag} className="usage-guide-stack-pill">
                  {tag}
                </span>
              ))}
            </div>
          </div>

          <FeaturedSection block={architectureFeatured} />

          <figure className="usage-guide-diagram" aria-label={L.diagramLabel}>
            <figcaption>{L.diagramLabel}</figcaption>
            <pre>{archDiagram}</pre>
          </figure>

          <FeaturedSection block={ragFeatured} />
          <FeaturedSection block={evalFeatured} />
          <FeaturedSection block={chatFeatured} />
          <FeaturedSection block={ingestFeatured} />
          <FeaturedSection block={authFeatured} />

          <p className="usage-guide-scroll-hint">{L.scrollHint}</p>
          <h3 className="usage-guide-workflow-title">{L.workflowLabel}</h3>
          {guideSections.map((section) => (
            <div key={section.label} className="usage-guide-section">
              <p className="usage-guide-section-label">{section.label}</p>
              <ol className="usage-guide-steps">
                {section.steps.map((step) => (
                  <li key={step.title}>
                    <strong>{step.title}</strong>
                    <p>{step.body}</p>
                    {step.items?.length ? (
                      <ul className="usage-guide-items">
                        {step.items.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    ) : null}
                  </li>
                ))}
              </ol>
            </div>
          ))}
          <p className="usage-guide-footer">{L.footer}</p>
        </div>
      ) : null}
    </div>
  );
}
