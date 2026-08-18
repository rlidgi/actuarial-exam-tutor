"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { useDocumentTitle } from "@/lib/use-document-title";
import {
  api,
  ApiError,
  isAuthError,
  type CategoryProgress,
  type ExamInfo,
  type ProgressSummary,
  type TopicProgress,
} from "@/lib/api";
import { useExam } from "@/lib/exam-context";
import { averageMastery, proficiencyTier, type ProficiencyTier } from "@/lib/proficiency";
import { TopicIcon } from "@/components/topic-icon";
import { DashboardSkeleton } from "@/components/skeleton";

export default function ProgressPage() {
  const { token, loading, redirectToExpiredLogin } = useRequireAuth();
  useDocumentTitle("Proficiency Dashboard");
  const { examCode, exams, setExamCode } = useExam();
  const [progress, setProgress] = useState<ProgressSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [subscribedExams, setSubscribedExams] = useState<ExamInfo[]>([]);
  // Tracks which exam `progress` was actually fetched for, so stale data
  // from the previously-selected exam is never shown after a switch --
  // adjusted during render (React's recommended alternative to resetting
  // state inside the effect itself), same idiom as chat/page.tsx's
  // newConversationSignal handling.
  const [loadedExamCode, setLoadedExamCode] = useState<string | null>(null);
  if (examCode !== loadedExamCode && progress !== null) {
    setLoadedExamCode(examCode);
    setProgress(null);
  }

  useEffect(() => {
    if (!token) return;
    api
      .getProgress(token, examCode)
      .then((summary) => {
        setProgress(summary);
        setLoadedExamCode(examCode);
      })
      .catch((err) => {
        if (isAuthError(err)) {
          redirectToExpiredLogin();
          return;
        }
        setError(err instanceof ApiError ? err.message : "Failed to load progress.");
      });
  }, [token, examCode, redirectToExpiredLogin]);

  // Only exams the user actually has an active subscription to belong in
  // the picker -- a 404/error for an exam with no StudentProfile yet reads
  // the same as "not subscribed" here, since either way it doesn't belong.
  useEffect(() => {
    if (!token || exams.length === 0) return;
    let cancelled = false;
    Promise.all(
      exams.map((exam) =>
        api
          .getBillingStatus(token, exam.code)
          .then((status) => (status.subscribed ? exam : null))
          .catch(() => null)
      )
    ).then((results) => {
      if (!cancelled) {
        setSubscribedExams(results.filter((exam): exam is ExamInfo => exam !== null));
      }
    });
    return () => {
      cancelled = true;
    };
  }, [token, exams]);

  if (loading || !token) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="flex-1 w-full overflow-y-auto">
      <div className="dashboard-page">
        <Link href="/chat" className="btn mb-2 inline-block">
          &larr; Back to Tutor
        </Link>
        <div className="dashboard-header">
          <h1>Proficiency Dashboard</h1>
          <p>
            Your per-topic proficiency across the full syllabus, a living picture that updates as
            you study -- not a one-time result.
          </p>
          {subscribedExams.length > 1 && (
            <ExamPicker
              exams={subscribedExams}
              activeCode={examCode}
              onSelect={(code) => void setExamCode(code)}
            />
          )}
        </div>

        {error && <div className="banner warn">{error}</div>}

        {!progress && !error && <p className="text-sm text-pencil text-center">Loading...</p>}

        {progress && (
          <>
            <SummaryStrip progress={progress} />
            <div className="topic-card-grid">
              {progress.categories.map((category) => (
                <CategoryCard key={category.name} category={category} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ExamPicker({
  exams,
  activeCode,
  onSelect,
}: {
  exams: ExamInfo[];
  activeCode: string;
  onSelect: (code: string) => void;
}) {
  return (
    <div className="exam-picker dashboard-exam-picker">
      {exams.map((exam) => (
        <button
          key={exam.code}
          type="button"
          className={`exam-card ${exam.code === activeCode ? "exam-card-active" : ""}`}
          onClick={() => onSelect(exam.code)}
        >
          <span className="exam-card-name">{exam.name}</span>
        </button>
      ))}
    </div>
  );
}

function SummaryStrip({ progress }: { progress: ProgressSummary }) {
  if (progress.topics_studied === 0) {
    return (
      <div className="dashboard-summary dashboard-summary-empty">
        <div className="summary-empty-icon" aria-hidden="true">
          <svg viewBox="0 0 64 64" width="44" height="44">
            <circle cx="32" cy="32" r="27" fill="none" stroke="var(--rule)" strokeWidth="4" />
            <path
              d="M32 5 A27 27 0 0 1 55 45"
              fill="none"
              stroke="var(--gold)"
              strokeWidth="4"
              strokeLinecap="round"
            />
            <circle cx="32" cy="32" r="5" fill="var(--ledger)" />
          </svg>
        </div>
        <div>
          <div className="summary-empty-title">No proficiency data yet</div>
          <p className="summary-empty-text">
            Start a conversation with the tutor to map your strengths and weaknesses across the
            full syllabus -- this dashboard fills in as you go.
          </p>
          <Link className="btn btn-primary" href="/chat">
            Start studying
          </Link>
        </div>
      </div>
    );
  }

  const allTopics = progress.categories.flatMap((c) => c.topics);
  const tierCounts: Record<ProficiencyTier, number> = { good: 0, warning: 0, critical: 0 };
  for (const topic of allTopics) {
    const { tier } = proficiencyTier(topic.mastery);
    if (tier) tierCounts[tier] += 1;
  }
  const { tier: overallTier } = proficiencyTier(progress.overall_mastery);

  return (
    <div className="dashboard-summary">
      <div className="summary-score">
        <div className="summary-score-value">
          {progress.overall_mastery}
          <span>%</span>
        </div>
        <div className="summary-score-label">Overall readiness</div>
        <div className="meter-track summary-meter-track">
          <div
            className={`meter-fill status-${overallTier ?? "critical"}`}
            style={{ width: `${progress.overall_mastery}%` }}
          />
        </div>
      </div>
      <div className="summary-chips">
        <span className="status-chip status-chip-critical status-chip-lg">
          {tierCounts.critical} weak
        </span>
        <span className="status-chip status-chip-warning status-chip-lg">
          {tierCounts.warning} developing
        </span>
        <span className="status-chip status-chip-good status-chip-lg">
          {tierCounts.good} strong
        </span>
      </div>
    </div>
  );
}

function CategoryCard({ category }: { category: CategoryProgress }) {
  const avgMastery = averageMastery(category.topics.map((t) => t.mastery));
  const { tier } = proficiencyTier(avgMastery);

  return (
    <section className={`topic-card status-edge-${tier ?? "empty"}`}>
      <div className="topic-card-header">
        <div className="topic-card-icon">
          <TopicIcon categoryName={category.name} />
        </div>
        <div className="topic-card-title">
          <h2>{category.name}</h2>
          {category.exam_weight != null && (
            <span className="topic-weight">~{category.exam_weight.toFixed(1)}% of exam</span>
          )}
        </div>
        {avgMastery !== null ? (
          <Meter mastery={avgMastery} />
        ) : (
          <span className="meter-empty">Not yet assessed</span>
        )}
      </div>

      <div className="outcome-list">
        {category.topics.map((topic) => (
          <TopicOutcomeRow key={topic.name} topic={topic} />
        ))}
      </div>
    </section>
  );
}

function TopicOutcomeRow({ topic }: { topic: TopicProgress }) {
  return (
    <div className="outcome-row">
      <span className="outcome-desc">{topic.name}</span>
      {topic.mastery !== null ? (
        <Meter mastery={topic.mastery} outcome />
      ) : (
        <span className="meter-empty">Not yet assessed</span>
      )}
    </div>
  );
}

function Meter({ mastery, outcome }: { mastery: number; outcome?: boolean }) {
  const { tier, label } = proficiencyTier(mastery);
  return (
    <div className={`meter-wrap ${outcome ? "outcome-meter-wrap" : ""}`}>
      <div className="meter-track">
        <div className={`meter-fill status-${tier}`} style={{ width: `${mastery}%` }} />
      </div>
      <span className="meter-value">{mastery}%</span>
      <span className={`status-chip status-chip-${tier}`}>{label}</span>
    </div>
  );
}
