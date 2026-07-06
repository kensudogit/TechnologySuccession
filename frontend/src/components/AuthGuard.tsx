"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getAuthStatus } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (pathname === "/login") return;

    getAuthStatus()
      .then((status) => {
        if (status.auth_enabled && !isLoggedIn()) {
          router.replace("/login");
        }
      })
      .catch(() => {});
  }, [pathname, router]);

  return <>{children}</>;
}
