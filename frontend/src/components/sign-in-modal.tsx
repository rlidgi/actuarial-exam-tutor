"use client";

import { useState, type FormEvent, type ReactNode } from "react";
import { useAuth } from "@/lib/auth-context";

export function SignInModal({
  onClose,
  banner,
}: {
  onClose: () => void;
  banner?: ReactNode;
}) {
  const { signInWithGoogle, sendMagicLink } = useAuth();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleGoogle = async () => {
    setError(null);
    try {
      // Full-page redirect to Google -- this call doesn't resolve into a
      // signed-in state here, the round trip lands on /auth/callback.
      await signInWithGoogle();
    } catch (err) {
      // Supabase's AuthError extends Error, so .message is Supabase's own
      // explanation (e.g. provider not enabled) -- more useful than a
      // generic message, and not misleading the way a fixed string would
      // be for causes unrelated to what it claims (see magic link below).
      setError(err instanceof Error ? err.message : "Couldn't start Google sign-in. Try again.");
    }
  };

  const handleMagicLink = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await sendMagicLink(email);
      setSent(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Couldn't send the link. Try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-sm rounded-lg bg-paper-raised p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-semibold text-ink">Sign in</h2>
          <button type="button" onClick={onClose} aria-label="Close" className="text-pencil">
            &times;
          </button>
        </div>

        {banner}

        <button
          type="button"
          onClick={handleGoogle}
          className="mb-4 w-full rounded-md border border-rule px-3 py-2 text-sm font-medium text-ink"
        >
          Continue with Google
        </button>

        <div className="mb-4 flex items-center gap-3 text-xs text-pencil-soft">
          <span className="h-px flex-1 bg-rule" />
          or
          <span className="h-px flex-1 bg-rule" />
        </div>

        {sent ? (
          <p className="text-sm text-pencil">
            Check your email for a sign-in link.
          </p>
        ) : (
          <form onSubmit={handleMagicLink} className="flex flex-col gap-3">
            <label className="flex flex-col gap-1 text-sm text-pencil">
              Email
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-md border border-rule bg-transparent px-3 py-2 text-ink"
              />
            </label>

            {error && <p className="text-sm text-redink">{error}</p>}

            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-ledger px-3 py-2 text-sm font-semibold text-paper disabled:opacity-50"
            >
              {submitting ? "Sending..." : "Send magic link"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
