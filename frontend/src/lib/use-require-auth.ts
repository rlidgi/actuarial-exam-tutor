"use client";

import { useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./auth-context";

// Redirects to /login if there's no token, and exposes a way to bail out to
// /login?expired=1 on a 401/422 from an API call. loggingOutRef (shared via
// AuthProvider, not local to this hook) guards against a race: logout()
// clearing `token` triggers the plain-redirect effect below in the same
// render pass as logout()'s own navigation, and without the guard the
// generic one fires after and wins, landing the user on /login regardless
// of where logout() actually sent them -- see auth-context.tsx.
export function useRequireAuth() {
  const { token, loading, logout, loggingOutRef } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !token && !loggingOutRef.current) {
      router.push("/login");
    }
  }, [loading, token, router, loggingOutRef]);

  // Stable identity: callers put this in effect dependency arrays, and a
  // new function reference every render would refetch on every unrelated
  // re-render.
  const redirectToExpiredLogin = useCallback(() => {
    logout("/login?expired=1");
  }, [logout]);

  return { token, loading, redirectToExpiredLogin };
}
