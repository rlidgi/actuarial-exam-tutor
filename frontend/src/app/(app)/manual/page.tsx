"use client";

import { useEffect, useState } from "react";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, EXAM_CODE, isAuthError } from "@/lib/api";

export default function ManualPage() {
  const { token, loading, redirectToExpiredLogin } = useRequireAuth();
  const [html, setHtml] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .getCourseHtml(token, EXAM_CODE)
      .then(setHtml)
      .catch((err) => {
        if (isAuthError(err)) {
          redirectToExpiredLogin();
          return;
        }
        setError(err instanceof ApiError ? err.message : "Failed to load the study manual.");
      });
  }, [token, redirectToExpiredLogin]);

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
      title="Exam P Study Manual"
      srcDoc={html}
      className="h-full w-full flex-1 border-0"
    />
  );
}
