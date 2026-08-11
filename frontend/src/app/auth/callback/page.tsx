"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";

// Redirect landing for both Google OAuth and magic-link sign-in -- supabase
// -js parses the URL (detectSessionInUrl) and establishes a Supabase
// session before this ever runs, so both flows share this one code path.
export default function AuthCallbackPage() {
  const { completeSupabaseSignIn } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | true | false>(false);

  useEffect(() => {
    // `ignore` guards against React's dev-mode double-invocation of effects
    // (mount -> cleanup -> mount): without it, a discarded first run could
    // still resolve after the real one and briefly redirect to the error
    // banner even though sign-in actually succeeded.
    let ignore = false;
    completeSupabaseSignIn()
      .then(() => {
        if (!ignore) router.replace("/chat");
      })
      .catch((err) => {
        // The flash message on the other end of this is deliberately vague
        // ("Sign-in didn't go through"), so without this the real cause
        // (network error, backend 500, Supabase rejecting the session,
        // etc.) is unrecoverable after the fact -- only the retry outcome
        // is observable, not why the first attempt failed.
        console.error("completeSupabaseSignIn failed:", err);
        if (ignore) return;
        // Only ApiError's message is guaranteed backend-crafted, user-facing
        // text (e.g. "already linked to a different sign-in method") --
        // anything else (network failure, Supabase-internal errors) could
        // read as a raw technical string, so those fall back to the generic
        // banner instead of surfacing err.message verbatim.
        setError(err instanceof ApiError ? err.message : true);
      });
    return () => {
      ignore = true;
    };
    // Intentionally run once -- completeSupabaseSignIn's identity is stable
    // (see auth-context.tsx) and re-running on every render would re-trigger
    // the exchange.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!error) return;
    const reason = typeof error === "string" ? `&reason=${encodeURIComponent(error)}` : "";
    router.replace(`/?signin_error=1${reason}`);
  }, [error, router]);

  return (
    <div className="flex min-h-dvh items-center justify-center">
      <p className="text-sm text-pencil">Signing you in...</p>
    </div>
  );
}
