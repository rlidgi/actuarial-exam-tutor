"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useRequireAuth } from "@/lib/use-require-auth";
import { useDocumentTitle } from "@/lib/use-document-title";
import { api, ApiError, isAuthError } from "@/lib/api";
import { useExam } from "@/lib/exam-context";
import { CardSkeleton } from "@/components/skeleton";

function SubscribeContent() {
  const { token, loading, redirectToExpiredLogin } = useRequireAuth();
  useDocumentTitle("Subscribe");
  const { examCode: currentExamCode } = useExam();
  const searchParams = useSearchParams();
  const examCode = searchParams.get("exam") || currentExamCode;
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubscribe = async () => {
    if (!token || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const { url } = await api.createCheckoutSession(token, examCode);
      window.location.href = url;
    } catch (err) {
      if (isAuthError(err)) {
        redirectToExpiredLogin();
        return;
      }
      setError(err instanceof ApiError ? err.message : "Couldn't start checkout. Try again.");
      setSubmitting(false);
    }
  };

  if (loading || !token) {
    return <CardSkeleton />;
  }

  return (
    <div className="flex flex-1 items-center justify-center p-6">
      <div className="w-full max-w-sm rounded-lg border border-rule bg-paper-raised p-6 text-center">
        <h1 className="mb-2 text-lg font-semibold text-ink">Subscribe to Exam {examCode}</h1>
        <p className="mb-4 text-sm text-pencil">
          $35/month for unlimited tutoring, practice problems, and proficiency tracking.
        </p>
        {error && <p className="mb-3 text-sm text-redink">{error}</p>}
        <button
          type="button"
          onClick={handleSubscribe}
          disabled={submitting}
          className="w-full rounded-md bg-ledger px-4 py-2 text-sm font-semibold text-paper hover:bg-ledger-bright disabled:opacity-50"
        >
          {submitting ? "Redirecting to Stripe..." : "Subscribe"}
        </button>
      </div>
    </div>
  );
}

export default function SubscribePage() {
  return (
    <Suspense fallback={null}>
      <SubscribeContent />
    </Suspense>
  );
}
