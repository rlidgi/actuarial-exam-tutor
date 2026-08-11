"use client";

import { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useBillingStatus } from "@/lib/use-billing-status";
import { api, ApiError, DEFAULT_EXAM_CODE, isAuthError } from "@/lib/api";
import { MarketingHeader } from "@/components/marketing-header";
import { SiteFooter } from "@/components/site-footer";

const EXAMS = [
  { code: "P", name: "Exam P -- Probability", price: 35 },
  { code: "FM", name: "Exam FM -- Financial Mathematics", price: 35 },
  { code: "FAM", name: "Exam FAM -- Fundamentals of Actuarial Mathematics", price: 35 },
];

const FEATURES = [
  "Unlimited tutor sessions",
  "Textbook citations",
  "Free study manual included",
  "Cancel anytime, no commitment",
];

const FREE_FEATURES = [
  "Study manual access for all 3 exams",
  "Up to 6 messages to try the tutor",
  "No credit card required",
];

export default function PricingContent() {
  const { token } = useAuth();
  const searchParams = useSearchParams();
  const highlightExam = searchParams.get("exam")?.toUpperCase() ?? null;

  // Real subscription status is only knowable for Exam P today -- FM/FAM
  // have no StudentProfile (and can't get one; there's no Exam row for
  // them yet), so there's nothing to check a subscription against.
  const { status: billingStatus } = useBillingStatus(token, DEFAULT_EXAM_CODE);

  const [subscribingCode, setSubscribingCode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubscribe = async (examCode: string) => {
    if (!token) return;
    setSubscribingCode(examCode);
    setError(null);
    try {
      const { url } = await api.createCheckoutSession(token, examCode);
      // Same pattern as subscribe/page.tsx and app-shell.tsx's
      // handleManageSubscription (both lint clean) -- a false positive
      // specific to this file's Suspense-wrapped inner-component structure
      // confusing the react-compiler plugin's static analysis, not a real
      // mutation-during-render issue (this only ever runs in a click handler).
      // eslint-disable-next-line react-hooks/immutability
      window.location.href = url;
    } catch (err) {
      if (isAuthError(err)) return;
      setError(
        err instanceof ApiError && err.status === 404
          ? `Exam ${examCode} isn't available yet -- check back soon!`
          : "Couldn't start checkout. Try again."
      );
    } finally {
      setSubscribingCode(null);
    }
  };

  return (
    <div className="landing">
      <MarketingHeader>
        {token ? (
          <>
            <Link className="btn" href="/progress">
              Proficiency Dashboard
            </Link>
            <Link className="btn" href="/chat">
              Back to Tutor
            </Link>
          </>
        ) : (
          <Link className="btn" href="/">
            Home
          </Link>
        )}
      </MarketingHeader>

      <div className="pricing-header">
        <h1>Pricing</h1>
      </div>

      {error && (
        <div className="banner warn pricing-notice">{error}</div>
      )}

      <div className="pricing-cards">
        <div className="pricing-card">
          <div className="pricing-card-name">Free</div>
          <div className="pricing-card-price">
            $0
            <span>/forever</span>
          </div>
          <ul className="pricing-card-features">
            {FREE_FEATURES.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
          <Link href={token ? "/chat" : "/register"} className="pricing-card-btn">
            {token ? "Go to chat" : "Get started free"}
          </Link>
        </div>
        {EXAMS.map((e) => {
          const isP = e.code === DEFAULT_EXAM_CODE;
          const subscribed = isP && billingStatus?.subscribed;
          return (
            <div
              key={e.code}
              className={`pricing-card ${e.code === highlightExam ? "highlighted" : ""}`}
            >
              <div className="pricing-card-name">{e.name}</div>
              <div className="pricing-card-price">
                ${e.price}
                <span>/month</span>
              </div>
              <ul className="pricing-card-features">
                {FEATURES.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
              {subscribed ? (
                <Link href="/chat" className="pricing-card-btn active">
                  Active
                </Link>
              ) : !token ? (
                <Link href="/register" className="pricing-card-btn">
                  Sign in to subscribe
                </Link>
              ) : (
                <button
                  type="button"
                  className="pricing-card-btn"
                  disabled={subscribingCode === e.code}
                  onClick={() => handleSubscribe(e.code)}
                >
                  {subscribingCode === e.code ? "Redirecting..." : "Subscribe"}
                </button>
              )}
            </div>
          );
        })}
      </div>

      <SiteFooter />
    </div>
  );
}
