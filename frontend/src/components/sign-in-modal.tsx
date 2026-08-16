"use client";

import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { useAuth } from "@/lib/auth-context";

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.91c1.7-1.57 2.69-3.88 2.69-6.62Z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.91-2.26c-.81.54-1.84.86-3.05.86-2.34 0-4.33-1.58-5.04-3.71H.96v2.33A9 9 0 0 0 9 18Z"
      />
      <path
        fill="#FBBC05"
        d="M3.96 10.71a5.4 5.4 0 0 1 0-3.42V4.96H.96a9 9 0 0 0 0 8.08l3-2.33Z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.32 0 2.51.46 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 0 0 .96 4.96l3 2.33C4.67 5.16 6.66 3.58 9 3.58Z"
      />
    </svg>
  );
}

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
  const [googleLoading, setGoogleLoading] = useState(false);
  const googleButtonRef = useRef<HTMLButtonElement>(null);
  const emailInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    googleButtonRef.current?.focus();

    // Prevent the landing page behind the modal from scrolling while it's open.
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleGoogle = async () => {
    setError(null);
    setGoogleLoading(true);
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
      setGoogleLoading(false);
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
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="sign-in-title"
        className="w-full max-w-sm rounded-lg bg-paper-raised p-6 shadow-lg"
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 id="sign-in-title" className="font-semibold text-ink">Sign in</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="-m-1.5 rounded-md p-1.5 text-lg leading-none text-pencil hover:text-redink"
          >
            &times;
          </button>
        </div>

        {banner}

        <button
          type="button"
          ref={googleButtonRef}
          onClick={handleGoogle}
          disabled={googleLoading}
          className="mb-4 flex w-full items-center justify-center gap-2 rounded-md border border-rule px-3 py-2 text-sm font-medium text-ink hover:border-ledger-bright disabled:opacity-50"
        >
          <GoogleIcon />
          {googleLoading ? "Redirecting..." : "Continue with Google"}
        </button>

        {error && <p className="mb-4 text-sm text-redink">{error}</p>}

        <div className="mb-4 flex items-center gap-3 text-xs text-pencil-soft">
          <span className="h-px flex-1 bg-rule" />
          or
          <span className="h-px flex-1 bg-rule" />
        </div>

        {sent ? (
          <div className="flex flex-col gap-3">
            <p className="text-sm text-pencil">
              Check <strong className="text-ink">{email}</strong> for a sign-in link.
            </p>
            <button
              type="button"
              onClick={() => {
                setSent(false);
                setError(null);
                setTimeout(() => emailInputRef.current?.focus(), 0);
              }}
              className="self-start text-sm text-pencil underline hover:text-ledger-bright"
            >
              Use a different email
            </button>
          </div>
        ) : (
          <form onSubmit={handleMagicLink} className="flex flex-col gap-3">
            <label className="flex flex-col gap-1 text-sm text-pencil">
              Email
              <input
                ref={emailInputRef}
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-md border border-rule bg-transparent px-3 py-2 text-ink"
              />
            </label>

            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-ledger px-3 py-2 text-sm font-semibold text-paper hover:bg-ledger-bright disabled:opacity-50"
            >
              {submitting ? "Sending..." : "Submit"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
