"use client";

import { useEffect, useState } from "react";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, isAuthError, type ProgressSummary, type TopicProgress } from "@/lib/api";

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
    <div className="flex-1 w-full overflow-y-auto">
      <div className="max-w-3xl w-full mx-auto p-6">
        <h1 className="text-lg font-semibold mb-4 text-ink">Your Progress -- Exam P</h1>

        {error && <p className="text-sm text-redink">{error}</p>}

        {!progress && !error && <p className="text-sm text-pencil">Loading...</p>}

        {progress && (
          <div className="flex flex-col gap-6">
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

            <div className="border border-rule bg-paper-raised rounded-lg p-4">
              <p className="text-sm font-medium mb-1 text-ink">Recommended next</p>
              <p className="text-sm text-ink">{progress.next_recommended_topic}</p>
              <p className="text-sm text-pencil mt-1">{progress.next_recommended_reason}</p>
            </div>

            <div className="flex flex-col gap-4">
              <h2 className="text-sm font-semibold text-pencil">Proficiency by topic</h2>
              {progress.categories.map((category) => (
                <div
                  key={category.name}
                  className="border border-rule bg-paper-raised rounded-lg p-4"
                >
                  <div className="flex items-baseline justify-between mb-3">
                    <h3 className="font-medium text-ink">{category.name}</h3>
                    {category.exam_weight != null && (
                      <span className="text-xs text-pencil">
                        ~{category.exam_weight.toFixed(1)}% of exam
                      </span>
                    )}
                  </div>
                  <div className="flex flex-col gap-2.5">
                    {category.topics.map((topic) => (
                      <TopicRow key={topic.name} topic={topic} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-rule bg-paper-raised rounded-lg p-4">
      <p className="text-xs text-pencil">{label}</p>
      <p className="text-xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function TopicRow({ topic }: { topic: TopicProgress }) {
  const started = topic.mastery !== null;
  const pct = started ? Math.max(0, Math.min(100, topic.mastery as number)) : 0;

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm flex-1 min-w-0 truncate text-ink" title={topic.name}>
        {topic.name}
      </span>
      <div className="w-28 h-1.5 rounded-full bg-rule overflow-hidden shrink-0">
        {started && <div className="h-full bg-ledger" style={{ width: `${pct}%` }} />}
      </div>
      <span className="text-xs text-pencil w-16 text-right shrink-0">
        {started ? `${topic.mastery}%` : "Not started"}
      </span>
    </div>
  );
}
