import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { AuthGuard } from "@/components/AuthGuard";

export const metadata: Metadata = {
  title: "TechnologySuccession RAG",
  description: "保全実績 RAG — トラブルシューティング支援",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body className="min-h-screen bg-slate-950 text-slate-100">
        <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
            <Link href="/" className="text-lg font-semibold text-emerald-400">
              TechnologySuccession
            </Link>
            <nav className="flex gap-4 text-sm">
              <Link href="/records" className="hover:text-emerald-400">Records</Link>
              <Link href="/chat" className="hover:text-emerald-400">Chat</Link>
              <Link href="/ingest" className="hover:text-emerald-400">Ingest</Link>
              <Link href="/eval" className="hover:text-emerald-400">Eval</Link>
              <Link href="/login" className="hover:text-emerald-400">Login</Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-8">
          <AuthGuard>{children}</AuthGuard>
        </main>
      </body>
    </html>
  );
}
