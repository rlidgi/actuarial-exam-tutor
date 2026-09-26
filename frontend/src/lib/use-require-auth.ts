"use client";

import { useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./auth-context";

// Where a signed-out visitor was headed when a protected page sent them to
// sign in (e.g. the feedback email's /feedback link) -- /auth/callback
// sends them back there instead of the default /chat. localStorage, not
// sessionStorage, so it survives a magic link opening in a new tab; kept
// for an hour so an abandoned attempt doesn't hijack a later, unrelated
// sign-in.
const POST_SIGN_IN_KEY = "aet_post_sign_in_path";
const POST_SIGN_IN_MAX_AGE_MS = 60 * 60 * 1000;

function rememberPostSignInPath() {
  try {
    const path = window.location.pathname + window.location.search;
    window.localStorage.setItem(POST_SIGN_IN_KEY, JSON.stringify({ path, at: Date.now() }));
  } catch {
    // Storage blocked -- sign-in just falls back to /chat.
  }
}

export function clearPostSignInPath() {
  try {
    window.localStorage.removeItem(POST_SIGN_IN_KEY);
  } catch {
    // ignore
  }
}

/** Reads and clears the remembered destination. Only same-site paths are
 * returned (never "//host" or a full URL), so it can't become an open
 * redirect. */
export function takePostSignInPath(): string | null {
  try {
    const raw = window.localStorage.getItem(POST_SIGN_IN_KEY);
    clearPostSignInPath();
    if (!raw) return null;
    const { path, at } = JSON.parse(raw);
    if (typeof path !== "string" || !path.startsWith("/") || path.startsWith("//")) return null;
    if (typeof at !== "number" || Date.now() - at > POST_SIGN_IN_MAX_AGE_MS) return null;
    return path;
  } catch {
    return null;
  }
}

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
      rememberPostSignInPath();
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
