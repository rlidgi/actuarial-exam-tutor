"use client";

import { useEffect, useState } from "react";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, isAuthError, type ProgressSummary } from "@/lib/api";

export default function ProgressPage() {
  const { token, loading, redirectToExpiredLogin } = useRequireAuth();
  const [progress, setProgress] = useState<ProgressSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api
      .getProgress(token)
      .then(setProgress)
      .catch((err) => {
        if (isAuthError(err)) {
          redirectToExpiredLogin();
          return;
        }
        setError(err instanceof ApiError ? err.message : "Failed to load progress.");
      });
  }, [token, redirectToExpiredLogin]);

  if (loading || !token) {
    return null;
  }

  return (
    <div className="flex-1 max-w-2xl w-full mx-auto p-6">
      <h1 className="text-lg font-semibold mb-4">Your Progress -- Exam P</h1>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {!progress && !error && <p className="text-sm text-black/50 dark:text-white/50">Loading...</p>}

      {progress && (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            <Stat label="Overall mastery" value={`${progress.overall_mastery}%`} />
            <Stat
              label="Topics studied"
              value={`${progress.topics_studied} / ${progress.topics_total}`}
            />
            <Stat label="Open mistakes" value={String(progress.open_mistakes)} />
            <Stat
              label="Weakest topic"
              value={
                progress.weakest_topic
                  ? `${progress.weakest_topic} (${progress.weakest_topic_mastery}%)`
                  : "None yet"
              }
            />
          </div>

          <div className="border border-black/10 dark:border-white/10 rounded-lg p-4">
            <p className="text-sm font-medium mb-1">Recommended next</p>
            <p className="text-sm">{progress.next_recommended_topic}</p>
            <p className="text-sm text-black/60 dark:text-white/60 mt-1">
              {progress.next_recommended_reason}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-black/10 dark:border-white/10 rounded-lg p-4">
      <p className="text-xs text-black/50 dark:text-white/50">{label}</p>
      <p className="text-xl font-semibold">{value}</p>
    </div>
  );
}
