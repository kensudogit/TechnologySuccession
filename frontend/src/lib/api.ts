const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function askQuestion(question: string, equipmentName?: string) {
  const res = await fetch(`${API_BASE}/chat/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, equipment_name: equipmentName }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getStats() {
  const res = await fetch(`${API_BASE}/records/stats`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function uploadFile(endpoint: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}${endpoint}`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function runEval() {
  const res = await fetch(`${API_BASE}/eval/run`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listRecords(equipmentName?: string) {
  const params = equipmentName ? `?equipment_name=${encodeURIComponent(equipmentName)}` : "";
  const res = await fetch(`${API_BASE}/records/${params}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function seedDatabase() {
  const res = await fetch(`${API_BASE}/admin/seed`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
