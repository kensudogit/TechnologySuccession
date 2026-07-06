"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getAuthStatus } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(pathname === "/login");

  useEffect(() => {
    if (pathname === "/login") {
      setReady(true);
      return;
    }

    let active = true;
    setReady(false);

    getAuthStatus()
      .then((status) => {
        if (!active) return;
        if (status.auth_enabled && !isLoggedIn()) {
          router.replace("/login");
          return;
        }
        setReady(true);
      })
      .catch(() => {
        if (active) setReady(true);
      });

    return () => {
      active = false;
    };
  }, [pathname, router]);

  if (!ready) {
    return <p className="text-slate-400">読み込み中...</p>;
  }

  return <>{children}</>;
}
