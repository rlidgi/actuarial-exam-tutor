"use client";

import { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useBillingStatus } from "@/lib/use-billing-status";
import { api, ApiError, DEFAULT_EXAM_CODE, isAuthError } from "@/lib/api";
import { SiteNav } from "@/components/site-nav";
import { SignInModal } from "@/components/sign-in-modal";
import { SiteFooter } from "@/components/site-footer";
import { EXAM_ICONS } from "@/components/exam-icons";

// Accent colors match landing-content.tsx's EXAMS (its exam cards use the
// same badge + icon treatment).
const EXAMS = [
  { code: "P", name: "Probability", price: 25, color: "#1f6fe5" },
  { code: "FM", name: "Financial Mathematics", price: 25, color: "#12a37f" },
  { code: "FAM", name: "Fundamentals of Actuarial Mathematics", price: 35, color: "#8250df" },
];

const FEATURES = [
  "Unlimited tutor sessions",
  "Textbook citations",
  "Free study manual included",
  "Formula sheet included",
  "Proficiency Dashboard",
  "Cancel anytime, no commitment",
];

const FREE_FEATURES = [
  "Study manual access for all 3 exams",
  "Formula sheet access for all 3 exams",
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
  const [showSignIn, setShowSignIn] = useState(false);

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
    <div className="landing pricing-page">
      {showSignIn && <SignInModal onClose={() => setShowSignIn(false)} />}

      {/* Same nav as the landing page -- the band wrapper supplies its
          docking/hamburger styles (see components/site-nav.tsx). */}
      <div className="landing-hero-band">
        <SiteNav onSignIn={() => setShowSignIn(true)} />
      </div>

      <div className="pricing-header">
        <p className="pricing-eyebrow">Pricing</p>
        <h1>Simple pricing, one exam at a time</h1>
        <p className="pricing-sub">
          Start free. Subscribe only to the exam you&apos;re studying for, and cancel anytime.
        </p>
      </div>

      {error && (
        <div className="banner warn pricing-notice">{error}</div>
      )}

      <div className="pricing-cards">
        <div className="pricing-card" style={{ "--exam-color": "#64748b" } as React.CSSProperties}>
          <div className="pricing-card-head">
            <span className="pricing-card-badge" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor"
                strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 6.5C10 5 7 4.5 3.5 5v13c3.5-.5 6.5 0 8.5 1.5 2-1.5 5-2 8.5-1.5V5C17 4.5 14 5 12 6.5Z" />
                <path d="M12 6.5v13" />
              </svg>
            </span>
            <div>
              <div className="pricing-card-name">Free</div>
              <div className="pricing-card-subname">Get started</div>
            </div>
          </div>
          <div className="pricing-card-price">
            $0
            <span>/forever</span>
          </div>
          <ul className="pricing-card-features">
            {FREE_FEATURES.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
          {!token && (
            <Link href="/register" className="pricing-card-btn">
              Get started free
            </Link>
          )}
        </div>
        {EXAMS.map((e) => {
          const isP = e.code === DEFAULT_EXAM_CODE;
          const subscribed = isP && billingStatus?.subscribed;
          return (
            <div
              key={e.code}
              className={`pricing-card ${e.code === highlightExam ? "highlighted" : ""}`}
              style={{ "--exam-color": e.color } as React.CSSProperties}
            >
              <div className="pricing-card-head">
                <span className="pricing-card-badge">{e.code}</span>
                <div>
                  <div className="pricing-card-name">Exam {e.code}</div>
                  <div className="pricing-card-subname">{e.name}</div>
                </div>
              </div>
              <div className="pricing-card-price">
                ${e.price}
                <span>/month</span>
                <span className="pricing-card-art" aria-hidden="true">
                  {EXAM_ICONS[e.code]?.(e.color)}
                </span>
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
                  Subscribe
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

      <div className="pricing-guarantee">
        <span className="pricing-guarantee-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor"
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z" />
            <path d="M8.5 12l2.5 2.5 4.5-5" />
          </svg>
        </span>
        <div>
          <strong>Pass Guarantee.</strong> If you take the exam and don&apos;t pass, we&apos;ll
          automatically extend your subscription by the number of months you originally paid
          for. And once you&apos;ve paid for 4 months total and still haven&apos;t passed,
          continued access is free for as long as you need it.
        </div>
      </div>

      <p className="pricing-help">
        Questions about plans? <Link href="/contact">Contact us</Link>.
      </p>

      <SiteFooter />
    </div>
  );
}
