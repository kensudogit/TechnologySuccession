"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getAuthStatus } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

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

    (async () => {
      for (let attempt = 0; attempt < 3; attempt += 1) {
        try {
          const status = await getAuthStatus();
          if (!active) return;
          if (status.auth_enabled && !isLoggedIn()) {
            router.replace("/login");
            return;
          }
          setReady(true);
          return;
        } catch {
          if (attempt === 2) {
            if (!active) return;
            if (isLoggedIn()) {
              setReady(true);
            } else {
              router.replace("/login");
            }
            return;
          }
          await sleep(400 * (attempt + 1));
        }
      }
    })();

    return () => {
      active = false;
    };
  }, [pathname, router]);

  if (!ready) {
    return <p className="text-slate-400">読み込み中...</p>;
  }

  return <>{children}</>;
}
