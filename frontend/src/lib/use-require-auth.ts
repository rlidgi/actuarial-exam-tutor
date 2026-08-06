"use client";

import { useCallback, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./auth-context";

// Redirects to /login if there's no token, and exposes a way to bail out to
// /login?expired=1 on a 401/422 from an API call. The ref guards against a
// race: logout() clearing `token` triggers the plain-redirect effect below
// in the same render pass as the caller's own navigation, and without the
// guard the generic one wins and strips the "expired" query param.
export function useRequireAuth() {
  const { token, loading, logout } = useAuth();
  const router = useRouter();
  const redirectingRef = useRef(false);

  useEffect(() => {
    if (!loading && !token && !redirectingRef.current) {
      router.push("/login");
    }
  }, [loading, token, router]);

  // Stable identity: callers put this in effect dependency arrays, and a
  // new function reference every render would refetch on every unrelated
  // re-render.
  const redirectToExpiredLogin = useCallback(() => {
    redirectingRef.current = true;
    logout();
    router.push("/login?expired=1");
  }, [logout, router]);

  return { token, loading, redirectToExpiredLogin };
}
