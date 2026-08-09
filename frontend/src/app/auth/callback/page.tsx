"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

// Redirect landing for both Google OAuth and magic-link sign-in -- supabase
// -js parses the URL (detectSessionInUrl) and establishes a Supabase
// session before this ever runs, so both flows share this one code path.
export default function AuthCallbackPage() {
  const { completeSupabaseSignIn } = useAuth();
  const router = useRouter();
  const [error, setError] = useState(false);

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
      .catch(() => {
        if (!ignore) setError(true);
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
    if (error) router.replace("/?signin_error=1");
  }, [error, router]);

  return (
    <div className="flex min-h-dvh items-center justify-center">
      <p className="text-sm text-pencil">Signing you in...</p>
    </div>
  );
}
