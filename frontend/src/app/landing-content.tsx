"use client";

import { Suspense, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { FAQ_ITEMS } from "@/lib/faq-data";
import { useReveal } from "@/lib/use-reveal";
import { MarketingHeader } from "@/components/marketing-header";
import { SiteFooter } from "@/components/site-footer";
import { MessageContent } from "@/components/message-content";
import { SignInModal } from "@/components/sign-in-modal";

const PREVIEW_ANSWER = `Let's work on **Combinatorics**, the recommended next topic. Your basic set reasoning is developing well, and counting methods will support many later probability problems.

**Diagnostic:**

A committee of 3 people is selected from 8 people. Does order matter?

A. Yes—use permutations

B. No—use combinations

Reply **A or B** and briefly say why.`;

const HERO_SYMBOLS: { text: string; left: string; top: string; fontSize: string; delay: string }[] = [
  { text: "Σ", left: "6%", top: "12%", fontSize: "2.1rem", delay: "0s" },
  { text: "∫", left: "90%", top: "18%", fontSize: "2.3rem", delay: "1.5s" },
  { text: "(1+i)ⁿ", left: "13%", top: "58%", fontSize: "1.25rem", delay: "3s" },
  { text: "δ", left: "85%", top: "60%", fontSize: "2rem", delay: "0.8s" },
  { text: "vⁿ", left: "4%", top: "78%", fontSize: "1.3rem", delay: "2.2s" },
  { text: "μ", left: "92%", top: "80%", fontSize: "1.7rem", delay: "4s" },
  { text: "σ²", left: "8%", top: "36%", fontSize: "1.4rem", delay: "5s" },
  { text: "∞", left: "93%", top: "42%", fontSize: "1.9rem", delay: "2.8s" },
  { text: "E[X]", left: "3%", top: "92%", fontSize: "1.15rem", delay: "1.2s" },
  { text: "λ", left: "88%", top: "6%", fontSize: "1.5rem", delay: "3.6s" },
  { text: "P(A∩B)", left: "16%", top: "4%", fontSize: "1.1rem", delay: "4.5s" },
  { text: "1−p", left: "80%", top: "92%", fontSize: "1.25rem", delay: "0.4s" },
  { text: "ₓpₓ", left: "20%", top: "8%", fontSize: "1.3rem", delay: "2s" },
  { text: "qₓ", left: "7%", top: "50%", fontSize: "1.2rem", delay: "3.3s" },
  { text: "Aₓ", left: "95%", top: "30%", fontSize: "1.6rem", delay: "1s" },
  { text: "äₓ", left: "22%", top: "88%", fontSize: "1.4rem", delay: "4.2s" },
  { text: "lₓ", left: "2%", top: "22%", fontSize: "1.15rem", delay: "0.6s" },
  { text: "eₓ", left: "78%", top: "14%", fontSize: "1.3rem", delay: "5.5s" },
  { text: "ₛEₓ", left: "83%", top: "70%", fontSize: "1.15rem", delay: "1.8s" },
  { text: "ω", left: "97%", top: "52%", fontSize: "1.8rem", delay: "3.8s" },
  { text: "ₛVₓ", left: "12%", top: "70%", fontSize: "1.1rem", delay: "2.6s" },
];

const EXAMS = [
  { code: "P", name: "Probability", color: "var(--sky)" },
  { code: "FM", name: "Financial Mathematics", color: "var(--gold)" },
  { code: "FAM", name: "Fundamentals of Actuarial Mathematics", color: undefined },
];

function SignInErrorBanner() {
  const searchParams = useSearchParams();
  if (searchParams.get("signin_error") !== "1") return null;

  return (
    <div className="banner warn pricing-notice">
      Sign-in didn&apos;t go through -- try again.
    </div>
  );
}

export default function LandingContent() {
  const { token, logout } = useAuth();
  const [showSignIn, setShowSignIn] = useState(false);
  useReveal();

  return (
    <div className="landing">
      <Suspense fallback={null}>
        <SignInErrorBanner />
      </Suspense>

      {showSignIn && <SignInModal onClose={() => setShowSignIn(false)} />}

      <MarketingHeader>
        <Link className="btn" href="/about">
          About
        </Link>
        <Link className="btn" href="/pricing">
          Pricing
        </Link>
        {token ? (
          <>
            <button type="button" className="btn" onClick={() => logout()}>
              Sign out
            </button>
            <Link className="btn btn-primary" href="/chat">
              Go to Tutor
            </Link>
          </>
        ) : (
          <button type="button" className="btn btn-primary" onClick={() => setShowSignIn(true)}>
            Sign in
          </button>
        )}
      </MarketingHeader>

      <div className="landing-hero">
        <div className="hero-bg" aria-hidden="true">
          <svg className="hero-curve" viewBox="0 0 800 300" preserveAspectRatio="none">
            <path d="M0,280 C150,270 300,220 450,140 C550,90 650,40 800,10" />
          </svg>
          {HERO_SYMBOLS.map((s, i) => (
            <span
              key={i}
              className="hero-symbol"
              style={{ left: s.left, top: s.top, fontSize: s.fontSize, animationDelay: s.delay }}
            >
              {s.text}
            </span>
          ))}
        </div>
        <h1>You don&apos;t have to go it alone.</h1>
        <p className="landing-hero-sub">
          You can have your own personal tutor for actuarial exams.
        </p>
        <div className="exam-picker">
          {EXAMS.map((e) => (
            <Link key={e.code} className="exam-card" href={`/pricing?exam=${e.code}`}>
              <span className="exam-card-code" style={e.color ? { color: e.color } : undefined}>
                {e.code}
              </span>
              <span className="exam-card-name">{e.name}</span>
            </Link>
          ))}
        </div>
        <div className="landing-free-banner">
          <p className="landing-free-banner-text">
            Register or log in for free access to the full study manual for each exam and 6 free
            messages to try out the AI tutor.
          </p>
          <button
            type="button"
            className="btn btn-primary landing-free-banner-btn"
            onClick={() => setShowSignIn(true)}
          >
            Get free access
          </button>
        </div>
      </div>

      <div className="preview-window reveal">
        <div className="preview-bar">
          <span className="preview-dot" />
          <span className="preview-dot" />
          <span className="preview-dot" />
          <span className="preview-exam">Exam P -- Probability</span>
        </div>
        <div className="preview-chat">
          <div className="bubble user">What should we work on next?</div>
          <div className="bubble assistant">
            <MessageContent text={PREVIEW_ANSWER} />
          </div>
        </div>
      </div>

      <div className="landing-features">
        <div className="feature-card reveal">
          <svg className="feature-illustration" viewBox="0 0 200 160" aria-hidden="true">
            <rect x="35" y="92" width="95" height="15" rx="2" fill="var(--gold)" />
            <rect x="42" y="77" width="85" height="15" rx="2" fill="var(--ledger)" />
            <rect x="49" y="62" width="75" height="15" rx="2" fill="var(--sky)" />
            <g className="mag-glass-group">
              <circle
                cx="140"
                cy="58"
                r="21"
                fill="rgba(246,247,241,0.9)"
                stroke="var(--ink)"
                strokeWidth="5"
              />
              <line
                x1="155"
                y1="73"
                x2="173"
                y2="91"
                stroke="var(--ink)"
                strokeWidth="6"
                strokeLinecap="round"
              />
            </g>
          </svg>
          <div className="feature-title">Grounded in your textbooks</div>
          <p>Every response is grounded in the exact SOA/CAS specified textbooks for that exam.</p>
        </div>
        <div className="feature-card reveal">
          <svg className="feature-illustration" viewBox="0 0 200 160" aria-hidden="true">
            <rect
              x="20"
              y="20"
              width="160"
              height="90"
              rx="16"
              fill="var(--paper-raised)"
              stroke="var(--ledger)"
              strokeWidth="2.5"
            />
            <path
              d="M60 110 L45 138 L82 110 Z"
              fill="var(--paper-raised)"
              stroke="var(--ledger)"
              strokeWidth="2.5"
            />
            <text
              x="100"
              y="80"
              fontSize="46"
              textAnchor="middle"
              fill="var(--ledger)"
              fontFamily="Georgia, serif"
              fontWeight="700"
            >
              ?
            </text>
          </svg>
          <div className="feature-title">Ask, or paste a problem</div>
          <p>Type a question, paste a problem, or work through practice problems the tutor generates for you.</p>
        </div>
        <div className="feature-card reveal">
          <Image
            className="feature-illustration feature-illustration-photo"
            src="/screenshotimage3.png"
            alt="A screenshot of a problem pasted into the tutor chat"
            width={220}
            height={147}
          />
          <div className="feature-title">Paste a screenshot</div>
          <p>Attach or paste an image of a problem straight into the chat. It&apos;s transcribed and answered like any typed question.</p>
        </div>
      </div>

      <div className="landing-faq">
        <h2>Questions</h2>
        {FAQ_ITEMS.map((item) => (
          <div key={item.question} className="faq-item reveal">
            <div className="faq-q">{item.question}</div>
            <p>{item.answer}</p>
          </div>
        ))}
      </div>

      <SiteFooter />
    </div>
  );
}
