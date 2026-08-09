"use client";

import { useEffect, useState } from "react";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, isAuthError } from "@/lib/api";
import { useExam } from "@/lib/exam-context";

export default function ManualPage() {
  const { token, loading, redirectToExpiredLogin } = useRequireAuth();
  const { examCode } = useExam();
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
    if (!token) return;
    api
      .getCourseHtml(token, examCode)
      .then((text) => {
        setHtml(text);
        setLoadedExamCode(examCode);
      })
      .catch((err) => {
        if (isAuthError(err)) {
          redirectToExpiredLogin();
          return;
        }
        setError(err instanceof ApiError ? err.message : "Failed to load the study manual.");
      });
  }, [token, examCode, redirectToExpiredLogin]);

  if (loading || !token) {
    return null;
  }

  if (error) {
    return <p className="p-6 text-sm text-redink">{error}</p>;
  }

  if (!html) {
    return <p className="p-6 text-sm text-pencil">Loading...</p>;
  }

  // The manual is a complete standalone document (its own <html>/<head>/CSS)
  // -- an iframe keeps its styles and any scripts isolated from the rest of
  // the app instead of colliding with it.
  return (
    <iframe
      title={`Exam ${examCode} Study Manual`}
      srcDoc={html}
      className="h-full w-full flex-1 border-0"
    />
  );
}
