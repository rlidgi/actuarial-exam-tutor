"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useDocumentTitle } from "@/lib/use-document-title";
import { api, ApiError } from "@/lib/api";
import { useExam } from "@/lib/exam-context";
import { DocumentSkeleton } from "@/components/skeleton";

// Public page -- the formula sheet needs no account, so this only reads
// useAuth() to decide which link the header CTA shows, never to gate access.
export default function FormulasPage() {
  const { token, loading: authLoading } = useAuth();
  useDocumentTitle("Formula Sheet");
  const { examCode, ready } = useExam();
  const [html, setHtml] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Tracks which exam `html` was actually fetched for, so a stale sheet
  // from the previously-selected exam is never shown after a switch --
  // adjusted during render (React's recommended alternative to resetting
  // state inside the effect itself), same idiom as manual/page.tsx's and
  // chat/page.tsx's newConversationSignal handling.
  const [loadedExamCode, setLoadedExamCode] = useState<string | null>(null);
  if (examCode !== loadedExamCode && html !== null) {
    setLoadedExamCode(examCode);
    setHtml(null);
  }

  useEffect(() => {
    // Wait for ExamProvider's one-time localStorage read -- examCode is
    // just a guessed default (DEFAULT_EXAM_CODE) until `ready`, and firing
    // a fetch for that guess would flash the wrong exam's sheet before the
    // render-time guard above discards it and re-fetches correctly.
    if (!ready) return;
    api
      .getFormulaSheetHtml(examCode)
      .then((text) => {
        setHtml(text);
        setLoadedExamCode(examCode);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Failed to load the formula sheet.");
      });
  }, [examCode, ready]);

  return (
    <div className="flex h-dvh w-full flex-col overflow-hidden bg-paper text-ink">
      {/* A real header row, not floated over the iframe like manual/page.tsx
          does -- the formula sheets have their own full-width sticky topbar
          with a control at top-right too (see static_content/formulas/*.html),
          so overlaying our own controls there collides with it. This way
          the iframe gets the remaining height below, no overlap possible
          regardless of what the embedded document does internally. */}
      <div className="flex flex-shrink-0 items-center justify-end gap-2 border-b border-rule bg-paper-raised px-3 py-2">
        <Link
          href="/"
          aria-label="Actuarial Exams Tutor -- home"
          title="Actuarial Exams Tutor -- home"
          className="flex h-9 w-9 items-center justify-center rounded-md border border-rule bg-paper shadow-sm hover:border-ledger-bright"
        >
          <Image src="/logo-mark.png" alt="" width={18} height={18} className="h-[18px] w-auto" />
        </Link>
        {!authLoading &&
          (token ? (
            <Link
              href="/chat"
              className="rounded-md border border-rule bg-paper px-3 py-2 text-sm text-ink shadow-sm hover:border-ledger-bright hover:text-ledger-bright"
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
        // The formula sheet is a complete standalone document (its own
        // <html>/<head>/CSS) -- an iframe keeps its styles and script
        // isolated from the rest of the app instead of colliding with it.
        <iframe
          title={`Exam ${examCode} Formula Sheet`}
          srcDoc={html}
          className="w-full flex-1 border-0"
        />
      )}
    </div>
  );
}
