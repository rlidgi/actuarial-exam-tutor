"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useDocumentTitle } from "@/lib/use-document-title";
import { api, ApiError } from "@/lib/api";
import { useExam } from "@/lib/exam-context";
import { DocumentSkeleton } from "@/components/skeleton";

// Public page -- the study manual needs no account, so this only reads
// useAuth() to decide which link the header CTA shows, never to gate access.
export default function ManualPage() {
  const { token, loading: authLoading } = useAuth();
  useDocumentTitle("Study Manual");
  const { examCode, ready } = useExam();
  const [html, setHtml] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Tracks which exam `html` was actually fetched for, so a stale manual
  // from the previously-selected exam is never shown after a switch --
  // adjusted during render (React's recommended alternative to resetting
  // state inside the effect itself), same idiom as chat/page.tsx's
  // newConversationSignal handling.
  const [loadedExamCode, setLoadedExamCode] = useState<string | null>(null);
  if (examCode !== loadedExamCode && html !== null) {
    setLoadedExamCode(examCode);
    setHtml(null);
  }

  useEffect(() => {
    // Wait for ExamProvider's one-time localStorage read -- examCode is
    // just a guessed default (DEFAULT_EXAM_CODE) until `ready`, and firing
    // a fetch for that guess would flash the wrong exam's manual before
    // the render-time guard above discards it and re-fetches correctly.
    if (!ready) return;
    api
      .getCourseHtml(examCode)
      .then((text) => {
        setHtml(text);
        setLoadedExamCode(examCode);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Failed to load the study manual.");
      });
  }, [examCode, ready]);

  return (
    <div className="h-dvh w-full overflow-hidden bg-paper text-ink">
      {/* Floating, top-right only -- the manual's own "Contents" toggle is
          fixed top-left inside the iframe (see static_content/courses/*.html).
          A full-width header row here would sit flush above that toggle's
          sidebar when it opens and read as a second stacked nav bar; keeping
          this to the opposite corner as small pill controls avoids that
          entirely instead of just disguising it. */}
      <div className="fixed right-3 top-3 z-50 flex items-center gap-2">
        <Link
          href="/"
          aria-label="Actuarial Exams Tutor -- home"
          title="Actuarial Exams Tutor -- home"
          className="flex h-9 w-9 items-center justify-center rounded-md border border-rule bg-paper-raised shadow-sm hover:border-ledger-bright"
        >
          <Image src="/logo-mark.png" alt="" width={18} height={18} className="h-[18px] w-auto" />
        </Link>
        {!authLoading &&
          (token ? (
            <Link
              href="/chat"
              className="rounded-md border border-rule bg-paper-raised px-3 py-2 text-sm text-ink shadow-sm hover:border-ledger-bright hover:text-ledger-bright"
            >
              &larr; Back to Tutor
            </Link>
          ) : (
            <Link
              href="/register"
              className="rounded-md border border-ledger-bright bg-ledger px-3 py-2 text-sm font-medium text-paper shadow-sm hover:bg-ledger-bright"
            >
              Try the tutor free &rarr;
            </Link>
          ))}
      </div>

      {error ? (
        <p className="p-6 text-sm text-redink">{error}</p>
      ) : !html ? (
        <DocumentSkeleton />
      ) : (
        // The manual is a complete standalone document (its own
        // <html>/<head>/CSS) -- an iframe keeps its styles and any scripts
        // isolated from the rest of the app instead of colliding with it.
        <iframe
          title={`Exam ${examCode} Study Manual`}
          srcDoc={html}
          className="h-full w-full border-0"
        />
      )}
    </div>
  );
}
