"use client";

import { Suspense, useId, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
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

const HERO_SYMBOLS: {
  text: string;
  left: string;
  top: string;
  fontSize: string;
  delay: string;
}[] = [
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
  {
    code: "FAM",
    name: "Fundamentals of Actuarial Mathematics",
    color: undefined,
  },
];

// P/FM/FAM icons on the exam-picker cards, in each exam's own accent color
// (matching EXAMS above) -- undefined falls back to the default ink color,
// same as exam-card-code already does for FAM.
const EXAM_ICONS: Record<string, (color: string) => React.JSX.Element> = {
  P: (color) => (
    <svg viewBox="0 0 40 40" width="44" height="44" aria-hidden="true">
      <line
        x1="6"
        y1="32"
        x2="34"
        y2="32"
        stroke="var(--rule)"
        strokeWidth="1.6"
      />
      <rect
        x="10"
        y="22"
        width="6"
        height="10"
        rx="1"
        fill={color}
        fillOpacity="0.75"
      />
      <rect
        x="19"
        y="15"
        width="6"
        height="17"
        rx="1"
        fill={color}
        fillOpacity="0.9"
      />
      <rect x="28" y="9" width="6" height="23" rx="1" fill={color} />
    </svg>
  ),
  FM: (color) => (
    <svg viewBox="0 0 40 40" width="44" height="44" aria-hidden="true">
      <path
        d="M6 28 L15 19 L21 24 L34 10"
        fill="none"
        stroke={color}
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M26 10 H34 V18"
        fill="none"
        stroke={color}
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ),
  FAM: (color) => (
    <svg viewBox="0 0 40 40" width="44" height="44" aria-hidden="true">
      <path
        d="M20 12 C17 9 11 8 6 9 V27 C11 26 17 27 20 30 C23 27 29 26 34 27 V9 C29 8 23 9 20 12 Z"
        fill="none"
        stroke={color}
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <line x1="20" y1="12" x2="20" y2="30" stroke={color} strokeWidth="1.8" />
    </svg>
  ),
};

// A more anatomically-detailed brain (outer lobe bumps + inner fold lines)
// than a plain silhouette would give -- drawn as one hemisphere, mirrored
// with a scale(-1,1) transform so both sides are guaranteed symmetric.
// useId keeps the <defs> id collision-safe if this ever renders more than
// once on a page.
function BrainIcon() {
  const hemiId = useId();
  return (
    <svg viewBox="0 0 40 40" width="66" height="66" aria-hidden="true">
      <defs>
        <g id={hemiId}>
          <path
            d="M20 9
               C22 7.3 24.5 7.3 26 9 C28 8 30.5 9.3 30.5 11.5
               C33 12 34.3 14.7 33 17 C34.5 18.6 34 21.3 32 22.3
               C32.8 23.6 32.5 25.3 31 26
               C31.3 28 29.7 29.8 27.6 29.8 C26.3 29.8 25.2 29.1 24.6 28.1
               C23.5 28.7 22.1 28.4 21.3 27.4 C20.6 27.7 20 27.3 20 26.5 Z"
            fill="none"
            stroke="var(--paper)"
            strokeWidth="1.3"
            strokeLinejoin="round"
          />
          <path
            d="M23 9.5 C25 10.8 25 13 23.3 14.5 C25.3 15.3 25.7 17.8 24 19.3"
            fill="none"
            stroke="var(--paper)"
            strokeWidth="1"
            strokeLinecap="round"
          />
          <path
            d="M29 12.5 C30.7 13.8 30.7 16 29 17.3 C30.7 18.3 30.8 20.7 29.2 21.8"
            fill="none"
            stroke="var(--paper)"
            strokeWidth="1"
            strokeLinecap="round"
          />
          <path
            d="M27.8 23 C29 24 29 25.7 27.7 26.6"
            fill="none"
            stroke="var(--paper)"
            strokeWidth="1"
            strokeLinecap="round"
          />
        </g>
      </defs>
      <use href={`#${hemiId}`} />
      <use href={`#${hemiId}`} transform="scale(-1,1) translate(-40,0)" />
      <line x1="20" y1="8.5" x2="20" y2="27.5" stroke="var(--paper)" strokeWidth="1.3" strokeOpacity="0.75" />
    </svg>
  );
}

function GiftIcon() {
  return (
    <svg viewBox="0 0 40 40" width="66" height="66" aria-hidden="true">
      <rect
        x="8"
        y="17"
        width="24"
        height="15"
        rx="1.5"
        fill="none"
        stroke="var(--paper)"
        strokeWidth="1.8"
      />
      <rect
        x="6"
        y="12"
        width="28"
        height="6"
        rx="1.5"
        fill="none"
        stroke="var(--paper)"
        strokeWidth="1.8"
      />
      <line
        x1="20"
        y1="12"
        x2="20"
        y2="32"
        stroke="var(--paper)"
        strokeWidth="1.6"
      />
      <path
        d="M20 12 C16 12 13 9.5 13 7.5 C13 6 14.3 5 15.8 5 C18 5 20 8 20 12 Z"
        fill="none"
        stroke="var(--paper)"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path
        d="M20 12 C24 12 27 9.5 27 7.5 C27 6 25.7 5 24.2 5 C22 5 20 8 20 12 Z"
        fill="none"
        stroke="var(--paper)"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function SignInErrorBanner() {
  const searchParams = useSearchParams();
  if (searchParams.get("signin_error") !== "1") return null;
  const reason = searchParams.get("reason");

  return (
    <div className="banner warn pricing-notice">
      {reason || "Sign-in didn't go through -- try again."}
    </div>
  );
}

export default function LandingContent() {
  const { token, logout } = useAuth();
  const router = useRouter();
  const [showSignIn, setShowSignIn] = useState(false);
  useReveal();

  // Sends visitors to that exam's overview page, which describes the free
  // and paid resources on offer and links to the free study manual/formula
  // sheet, instead of dropping them straight into sign-in.
  const handleExamClick = (code: string) => {
    router.push(`/exams/${code}`);
  };

  return (
    <div className="landing">
      <Suspense fallback={null}>
        <SignInErrorBanner />
      </Suspense>

      {showSignIn && <SignInModal onClose={() => setShowSignIn(false)} />}

      <div className="landing-hero-band">
        <div className="hero-bg" aria-hidden="true">
          {HERO_SYMBOLS.map((s, i) => (
            <span
              key={i}
              className="hero-symbol"
              style={{
                left: s.left,
                top: s.top,
                fontSize: s.fontSize,
                animationDelay: s.delay,
              }}
            >
              {s.text}
            </span>
          ))}
        </div>
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
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setShowSignIn(true)}
            >
              Sign in
            </button>
          )}
        </MarketingHeader>

        <div className="landing-hero">
          <h1>Your personal tutor for actuarial exams</h1>
          <div
            className="landing-hero-tagline"
            // will-change stays in the CSS for the animation itself, but
            // leaving it on indefinitely keeps this promoted to its own
            // compositing layer forever -- releasing it once the one-shot
            // entrance animation finishes avoids that ongoing overhead
            // (was showing up as sluggish hover transitions elsewhere on
            // the page, e.g. the exam-picker cards).
            onAnimationEnd={(e) => {
              e.currentTarget.style.willChange = "auto";
            }}
          >
            <span className="tagline-line" aria-hidden="true" />
            <span>You don&apos;t have to go it alone.</span>
            <span className="tagline-line" aria-hidden="true" />
          </div>
          <div className="landing-hero-feature">
            <span className="landing-hero-feature-icon">
              <BrainIcon />
            </span>
            <div className="landing-hero-feature-text">
              <div className="landing-hero-feature-title">
                Personalized guidance from an AI tutor that adapts as you learn.
              </div>
              <p>
                Your tutor tracks what you&apos;ve mastered, identifies gaps in
                your foundational knowledge, and guides you step by step toward
                exam mastery.
              </p>
            </div>
          </div>
          <div className="exam-picker">
            {EXAMS.map((e) => (
              <button
                key={e.code}
                type="button"
                className="exam-card"
                onClick={() => handleExamClick(e.code)}
              >
                <span
                  className="exam-card-code"
                  style={e.color ? { color: e.color } : undefined}
                >
                  {e.code}
                </span>
                <span className="exam-card-name">{e.name}</span>
                {EXAM_ICONS[e.code]?.(e.color ?? "var(--ink)")}
              </button>
            ))}
          </div>
          <div className="landing-free-banner">
            <span className="landing-hero-feature-icon">
              <GiftIcon />
            </span>
            <div className="landing-free-banner-text">
              <div className="landing-hero-feature-title">
                Experience a tutor that adapts to you.
              </div>
              <p>
                The study manual and formula sheet are free for everyone, no account
                needed. Sign up free to get 6 messages to try out the AI tutor.
              </p>
            </div>
            <button
              type="button"
              className="btn landing-free-banner-btn"
              onClick={() => setShowSignIn(true)}
            >
              Sign up free &rarr;
            </button>
          </div>
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
          <Image
            className="feature-illustration"
            src="/books-v3.webp"
            alt="An icon of a stack of books with a magnifying glass, representing textbook-grounded answers"
            width={300}
            height={200}
          />
          <div className="feature-title">Grounded in your textbooks</div>
          <p>
            Every response is grounded in the exact SOA/CAS specified textbooks
            for that exam. When appropriate, cites text directly and provides
            page number and textbook name for further study.
          </p>
        </div>
        <div className="feature-card reveal">
          <Image
            className="feature-illustration"
            src="/problem-v3.webp"
            alt="An icon of a question bubble next to an image with a copy badge, representing asking or pasting a problem"
            width={300}
            height={200}
          />
          <div className="feature-title">Help with a problem</div>
          <p>
            Attach an image or paste a screenshot of a problem. Instead of
            simply giving you the answer, the tutor works through the problem
            with you step by step, helping you understand how to solve it.
          </p>
        </div>
        <div className="feature-card reveal">
          <Image
            className="feature-illustration"
            src="/growth-icon-v2.webp"
            alt="An icon of a student in a circle next to a rising bar chart, representing adaptive progress tracking"
            width={300}
            height={200}
          />
          <div className="feature-title">Personalized learning that adapts</div>
          <p>
            The actuarial tutor adapts to each student&apos;s unique needs, much
            like a human tutor. It continuously tracks proficiency, strengthens
            foundational knowledge where needed, and guides students step by
            step toward mastery.
          </p>
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
