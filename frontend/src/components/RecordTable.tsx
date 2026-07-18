import type { MaintenanceRecord } from "@/lib/records";

type Props = {
  records: MaintenanceRecord[];
  compact?: boolean;
};

export function RecordTable({ records, compact = false }: Props) {
  if (records.length === 0) {
    return (
      <p className="text-sm text-slate-500">保全実績データがありません。</p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-slate-900 text-slate-400">
          <tr>
            <th className="px-4 py-3 whitespace-nowrap">日付</th>
            <th className="px-4 py-3 whitespace-nowrap">設備名</th>
            <th className="px-4 py-3 whitespace-nowrap">ライン</th>
            <th className="px-4 py-3 whitespace-nowrap">症状</th>
            {!compact && <th className="px-4 py-3 whitespace-nowrap">原因</th>}
            <th className="px-4 py-3 whitespace-nowrap">処置</th>
            {!compact && <th className="px-4 py-3 whitespace-nowrap">担当</th>}
            <th className="px-4 py-3 whitespace-nowrap">出典</th>
          </tr>
        </thead>
        <tbody>
          {records.map((r) => (
            <tr key={r.id} className="border-t border-slate-800 hover:bg-slate-900/50">
              <td className="px-4 py-3 whitespace-nowrap">{r.event_date ?? "—"}</td>
              <td className="px-4 py-3 whitespace-nowrap font-medium text-emerald-400">
                {r.equipment_name ?? "—"}
              </td>
              <td className="px-4 py-3 whitespace-nowrap">{r.line_name ?? "—"}</td>
              <td className="px-4 py-3 max-w-xs truncate">{r.symptom ?? "—"}</td>
              {!compact && <td className="px-4 py-3 max-w-xs truncate">{r.root_cause ?? "—"}</td>}
              <td className="px-4 py-3 max-w-xs truncate">{r.action_taken ?? "—"}</td>
              {!compact && <td className="px-4 py-3">{r.inspector ?? "—"}</td>}
              <td className="px-4 py-3 text-xs text-slate-500">{r.source_file ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
