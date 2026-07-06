"use client";

import { useState } from "react";
import { askQuestion } from "@/lib/api";

type Source = {
  record_id: string;
  equipment_name?: string;
  event_date?: string;
  source_file?: string;
  excerpt?: string;
};

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [equipment, setEquipment] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [confidence, setConfidence] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await askQuestion(question, equipment || undefined);
      setAnswer(res.answer);
      setSources(res.sources || []);
      setConfidence(res.confidence);
    } catch (err) {
      setAnswer(`エラー: ${err}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2 space-y-4">
        <h1 className="text-2xl font-bold">トラブルシューティング Chat</h1>
        <form onSubmit={handleAsk} className="space-y-3">
          <input
            value={equipment}
            onChange={(e) => setEquipment(e.target.value)}
            placeholder="設備名（任意）例: コンプレッサA-03"
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2"
          />
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="例: 異音が出ている。過去に似た事例は？"
            rows={4}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2"
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-emerald-600 px-6 py-2 font-medium hover:bg-emerald-500 disabled:opacity-50"
          >
            {loading ? "検索中..." : "質問する"}
          </button>
        </form>

        {answer && (
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <div className="mb-3 flex items-center gap-2">
              <span className="text-sm text-slate-400">信頼度:</span>
              <span
                className={`rounded px-2 py-0.5 text-xs ${
                  confidence === "high"
                    ? "bg-emerald-900 text-emerald-300"
                    : confidence === "medium"
                    ? "bg-yellow-900 text-yellow-300"
                    : "bg-red-900 text-red-300"
                }`}
              >
                {confidence}
              </span>
            </div>
            <pre className="whitespace-pre-wrap text-sm leading-relaxed">{answer}</pre>
          </div>
        )}
      </div>

      <aside className="space-y-4">
        <h2 className="font-semibold">参考実績</h2>
        {sources.length === 0 && (
          <p className="text-sm text-slate-500">質問すると引用元が表示されます</p>
        )}
        {sources.map((s) => (
          <div key={s.record_id} className="rounded-lg border border-slate-800 bg-slate-900 p-4 text-sm">
            <p className="font-medium text-emerald-400">{s.equipment_name}</p>
            <p className="text-slate-400">{s.event_date} — {s.source_file}</p>
            <p className="mt-2 text-slate-300">{s.excerpt}</p>
          </div>
        ))}
      </aside>
    </div>
  );
}
