"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { MarketingHeader } from "@/components/marketing-header";
import { SiteFooter } from "@/components/site-footer";
import { SignInModal } from "@/components/sign-in-modal";
import { AppLink, navigateToApp } from "@/components/app-link";
import { EXAM_OVERVIEW, type ExamCode } from "./exam-overview-data";
import { TOPIC_ICONS } from "./topic-icons";

const PAID_FEATURES = [
  "Unlimited tutor sessions",
  "Textbook citations",
  "Free study manual included",
  "Formula sheet included",
  "Proficiency Dashboard",
  "Cancel anytime, no commitment",
];

// Same key exam-context.tsx persists the selected exam under, and
// auth-context.tsx's afterAuth reads at signup -- redefined locally rather
// than imported, same reasoning as landing-content.tsx's own copy.
const EXAM_STORAGE_KEY = "actuarial_tutor_exam";

export default function ExamOverviewContent({ code }: { code: ExamCode }) {
  const { token, logout } = useAuth();
  const router = useRouter();
  const [showSignIn, setShowSignIn] = useState(false);
  const exam = EXAM_OVERVIEW[code];

  // Persists which exam these links are about, purely so /manual and
  // /formulas (each wrapped in its own ExamProvider) pick the right one up
  // on mount -- these are public pages now, so this never gates access,
  // just pre-selects.
  const setExamStorage = () => {
    window.localStorage.setItem(EXAM_STORAGE_KEY, code);
  };

  // Trying the tutor still needs an account -- lands a signed-in visitor
  // straight on /chat, or opens sign-in for a signed-out one, same pattern
  // as landing-content.tsx and the free-access banner there.
  const handleTryTutor = () => {
    setExamStorage();
    if (token) {
      navigateToApp(router, "/chat");
    } else {
      setShowSignIn(true);
    }
  };

  return (
    <div className="landing">
      {showSignIn && <SignInModal onClose={() => setShowSignIn(false)} />}

      <MarketingHeader>
        <AppLink className="btn" href="/about">
          About
        </AppLink>
        <AppLink className="btn" href="/pricing">
          Pricing
        </AppLink>
        {token ? (
          <>
            <button type="button" className="btn" onClick={() => logout()}>
              Sign out
            </button>
            <AppLink className="btn btn-primary" href="/chat">
              Go to Tutor
            </AppLink>
          </>
        ) : (
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setShowSignIn(true)}
          >
            Sign in
          </button>
        )}
      </MarketingHeader>

      <div className="pricing-header">
        <h1>
          Exam {code} - {exam.shortName}
        </h1>
        <p className="exam-overview-tagline">{exam.tagline}</p>
      </div>

      <div className="exam-overview-section">
        <h2>What Exam {code} covers</h2>
        <div className="topic-cards">
          {exam.topics.map((topic) => {
            const Icon = TOPIC_ICONS[topic.icon];
            return (
              <div key={topic.title} className="topic-card">
                <span
                  className="topic-card-icon"
                  style={exam.accent ? { background: exam.accent } : undefined}
                >
                  <Icon />
                </span>
                <div className="topic-card-title">{topic.title}</div>
                <ul className="topic-card-points">
                  {topic.points.map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>

      <div className="exam-overview-section">
        <h2>Exam Resources</h2>
        <p>
          The study manual and formula sheet are free for everyone, no account needed.
          Sign up free for 6 messages to try the AI tutor, or subscribe for unlimited
          tutoring on {exam.fullName}.
        </p>
      </div>

      <div className="exam-overview-cards">
        <div className="pricing-card">
          <div className="pricing-card-name">Free Resources</div>
          <p className="exam-overview-card-note">No account needed</p>
          <ul className="pricing-card-features">
            <li>Full study manual for {exam.fullName}</li>
            <li>Formula sheet for {exam.fullName}</li>
          </ul>
          <div className="exam-overview-actions">
            <AppLink href="/manual" className="pricing-card-btn" onClick={setExamStorage}>
              View Study Manual
            </AppLink>
            <AppLink href="/formulas" className="pricing-card-btn" onClick={setExamStorage}>
              View Formula Sheet
            </AppLink>
          </div>
        </div>

        <div className="pricing-card">
          <div className="pricing-card-name">Free Account</div>
          <ul className="pricing-card-features">
            <li>Up to 6 messages to try the AI tutor</li>
            <li>No credit card required</li>
          </ul>
          <div className="exam-overview-actions">
            <button type="button" className="pricing-card-btn" onClick={handleTryTutor}>
              {token ? "Go to Tutor" : "Sign up free"}
            </button>
          </div>
        </div>

        <div className="pricing-card">
          <div className="pricing-card-name">{exam.fullName}</div>
          <div className="pricing-card-price">
            ${exam.price}
            <span>/month</span>
          </div>
          <ul className="pricing-card-features">
            {PAID_FEATURES.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
          <button
            type="button"
            className="pricing-card-btn"
            onClick={() => navigateToApp(router, `/pricing?exam=${code}`)}
          >
            See pricing &amp; subscribe
          </button>
        </div>
      </div>

      <SiteFooter />
    </div>
  );
}
