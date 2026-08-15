"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRequireAuth } from "@/lib/use-require-auth";
import { api, ApiError, isAuthError, type ReferralSummary } from "@/lib/api";

const REWARD_LABELS: Record<ReferralSummary["rewards"][number]["reward_type"], string> = {
  referred_percent_off: "25% off your first month",
  referrer_percent_off: "25% off your next month",
  referrer_free_month: "One free month",
};

const STATUS_LABELS: Record<ReferralSummary["rewards"][number]["status"], string> = {
  pending: "Pending",
  applied: "Applied",
  failed: "Failed",
};

export default function AccountPage() {
  const { token, loading, redirectToExpiredLogin } = useRequireAuth();
  const [summary, setSummary] = useState<ReferralSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!token) return;
    api
      .getReferralSummary(token)
      .then(setSummary)
      .catch((err) => {
        if (isAuthError(err)) {
          redirectToExpiredLogin();
          return;
        }
        setError(err instanceof ApiError ? err.message : "Failed to load referral info.");
      });
  }, [token, redirectToExpiredLogin]);

  const handleCopy = async () => {
    if (!summary) return;
    await navigator.clipboard.writeText(summary.referral_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading || !token) {
    return null;
  }

  return (
    <div className="flex-1 w-full overflow-y-auto">
      <div className="dashboard-page">
        <Link href="/chat" className="btn mb-2 inline-block">
          &larr; Back to Tutor
        </Link>
        <div className="dashboard-header">
          <h1>Referrals</h1>
          <p>
            Share your link. When someone you refer subscribes, they get 25% off their first
            month, and you get 25% off your next month -- every 3rd referral earns you a full
            free month instead.
          </p>
        </div>

        {error && <div className="banner warn">{error}</div>}

        {!summary && !error && <p className="text-sm text-pencil text-center">Loading...</p>}

        {summary && (
          <>
            <div className="rounded-lg border border-rule bg-paper-raised p-6">
              <label className="mb-2 block text-sm font-semibold text-ink">
                Your referral link
              </label>
              <div className="flex flex-col gap-2 sm:flex-row">
                <input
                  type="text"
                  readOnly
                  value={summary.referral_url}
                  onFocus={(e) => e.target.select()}
                  className="w-full flex-1 rounded-md border border-rule bg-paper px-3 py-2 text-sm text-ink"
                />
                <button
                  type="button"
                  onClick={handleCopy}
                  className="rounded-md bg-ledger px-4 py-2 text-sm font-semibold text-paper hover:bg-ledger-bright"
                >
                  {copied ? "Copied!" : "Copy link"}
                </button>
              </div>
              <p className="mt-3 text-sm text-pencil">
                Completed referrals:{" "}
                <span className="font-semibold text-ink">{summary.completed_referral_count}</span>
              </p>
            </div>

            <div className="mt-6">
              <h2 className="mb-2 text-lg font-semibold text-ink">Reward history</h2>
              {summary.rewards.length === 0 ? (
                <p className="text-sm text-pencil">
                  No rewards yet -- share your link to start earning discounts.
                </p>
              ) : (
                <div className="flex flex-col gap-2">
                  {summary.rewards.map((reward, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between rounded-md border border-rule bg-paper-raised px-4 py-3"
                    >
                      <span className="text-sm text-ink">{REWARD_LABELS[reward.reward_type]}</span>
                      <span className="status-chip">{STATUS_LABELS[reward.status]}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
