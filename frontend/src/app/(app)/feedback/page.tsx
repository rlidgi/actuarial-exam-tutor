"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, isAuthError, type FeedbackCategory } from "@/lib/api";
import { DashboardSkeleton } from "@/components/skeleton";

const RATING_FIELDS = [
  { key: "overall_rating", label: "How would you rate your experience?" },
  { key: "tutor_quality_rating", label: "How helpful were the AI Tutor's answers?" },
  { key: "ease_of_use_rating", label: "How easy is the site to use?" },
  { key: "value_rating", label: "Does it feel worth the price?" },
] as const;

type RatingKey = (typeof RATING_FIELDS)[number]["key"];
type Ratings = Record<RatingKey, number | null>;

const CATEGORIES: { value: FeedbackCategory; label: string }[] = [
  { value: "bug", label: "Bug" },
  { value: "feature_request", label: "Feature request" },
  { value: "ui_ux", label: "UI / UX" },
  { value: "performance", label: "Performance" },
  { value: "other", label: "Other" },
];

const SERIF_FONT = 'ui-serif, "Iowan Old Style", "Palatino Linotype", Georgia, serif';

function RatingRow({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number | null;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      <span className="text-sm font-medium text-ink">{label}</span>
      <div className="flex gap-2" role="radiogroup" aria-label={label}>
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            role="radio"
            aria-checked={value === n}
            onClick={() => onChange(n)}
            className={`flex h-9 w-9 items-center justify-center rounded-full border text-sm font-medium transition-colors ${
              value === n
                ? "border-ledger bg-ledger text-paper"
                : "border-rule text-ink hover:border-ledger-bright"
            }`}
          >
            {n}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function FeedbackPage() {
  const { token, loading, redirectToExpiredLogin } = useRequireAuth();
  const [ratings, setRatings] = useState<Ratings>({
    overall_rating: null,
    tutor_quality_rating: null,
    ease_of_use_rating: null,
    value_rating: null,
  });
  const [category, setCategory] = useState<FeedbackCategory | null>(null);
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (loading || !token) {
    return <DashboardSkeleton />;
  }

  const setRating = (key: RatingKey, value: number) =>
    setRatings((prev) => ({ ...prev, [key]: value }));

  const hasAnyAnswer =
    Object.values(ratings).some((v) => v !== null) || category !== null || message.trim() !== "";

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || !hasAnyAnswer) return;
    setError(null);
    setSubmitting(true);
    try {
      await api.submitFeedback(token, {
        ...ratings,
        category,
        message: message.trim() || null,
      });
      setSent(true);
    } catch (err) {
      if (isAuthError(err)) {
        redirectToExpiredLogin();
        return;
      }
      setError(err instanceof ApiError ? err.message : "Couldn't send feedback. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex-1 w-full overflow-y-auto">
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
        <Link href="/chat" className="btn mb-4 inline-block">
          &larr; Back to Tutor
        </Link>

        <div className="grid overflow-hidden rounded-lg border border-rule md:grid-cols-2">
          <div className="flex flex-col gap-6 bg-gradient-to-br from-ink to-ledger p-8 text-paper">
            <span className="text-xs font-semibold uppercase tracking-wide text-paper/60">
              Product Feedback
            </span>
            <h1 className="text-3xl font-bold" style={{ fontFamily: SERIF_FONT }}>
              Help us improve Actuarial Exams Tutor
            </h1>
            <p className="text-paper/80">
              This form is for product feedback -- ideas, bugs, and what&rsquo;s working or not. If
              you need account or billing help, use{" "}
              <Link href="/contact" className="underline hover:text-paper">
                Contact Us
              </Link>{" "}
              instead.
            </p>
            <div className="rounded-lg bg-white/10 p-4">
              <h2 className="mb-2 font-semibold">Good feedback includes</h2>
              <ul className="list-disc pl-5 text-sm text-paper/80">
                <li>What you were trying to do</li>
                <li>What happened vs. what you expected</li>
                <li>Which exam or topic it relates to</li>
              </ul>
            </div>
            <p className="mt-auto text-sm text-paper/60">
              We read every submission. This data directly shapes what we build next.
            </p>
          </div>

          <div className="flex flex-col gap-5 bg-paper-raised p-8">
            <h2 className="text-xl font-semibold text-ink">Send feedback</h2>

            {sent ? (
              <p className="text-sm text-ink">
                Thanks for the feedback -- we read every submission and it directly shapes what we
                build next.
              </p>
            ) : (
              <form onSubmit={handleSubmit} className="flex flex-col gap-5">
                {RATING_FIELDS.map((f) => (
                  <RatingRow
                    key={f.key}
                    label={f.label}
                    value={ratings[f.key]}
                    onChange={(v) => setRating(f.key, v)}
                  />
                ))}
                <p className="-mt-3 text-xs text-pencil-soft">Every question here is optional.</p>

                <div className="flex flex-col gap-2">
                  <span className="text-sm font-medium text-ink">What is this about?</span>
                  <div className="flex flex-wrap gap-2">
                    {CATEGORIES.map((c) => (
                      <button
                        key={c.value}
                        type="button"
                        aria-pressed={category === c.value}
                        onClick={() => setCategory(category === c.value ? null : c.value)}
                        className={`rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${
                          category === c.value
                            ? "border-ledger bg-ledger text-paper"
                            : "border-rule text-ledger hover:border-ledger-bright"
                        }`}
                      >
                        {c.label}
                      </button>
                    ))}
                  </div>
                </div>

                <label className="flex flex-col gap-1 text-sm font-medium text-ink">
                  Your feedback
                  <textarea
                    rows={5}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Tell us what you liked, what needs improvement, or what went wrong..."
                    className="rounded-md border border-rule bg-transparent px-3 py-2 font-normal text-ink"
                  />
                </label>
                <p className="-mt-3 text-xs text-pencil-soft">
                  You can submit with just a rating, but a short message helps a lot.
                </p>

                {error && <p className="text-sm text-redink">{error}</p>}

                <button
                  type="submit"
                  disabled={submitting || !hasAnyAnswer}
                  className="rounded-md bg-ledger px-4 py-2 text-sm font-semibold text-paper hover:bg-ledger-bright disabled:opacity-50"
                >
                  {submitting ? "Sending..." : "Send feedback"}
                </button>
                <Link
                  href="/contact"
                  className="rounded-md border border-rule px-4 py-2 text-center text-sm text-ink hover:border-ledger-bright hover:text-ledger-bright"
                >
                  Need help instead?
                </Link>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
