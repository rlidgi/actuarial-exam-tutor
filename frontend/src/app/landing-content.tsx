"use client";

import { Suspense, useState } from "react";
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

// Small outline icons for the hero's 3-item feature row and the "Built for
// your success" row below the exam cards -- BarsIcon and TargetIcon are
// deliberately reused across both rows (matching mastery-tracking /
// focused-practice, the two rows' closest thematic overlap), same as the
// reference design reusing its own icon vocabulary rather than drawing a
// new glyph for every single item.
function BarsIcon() {
  return (
    <svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true">
      <rect x="7" y="21" width="6" height="12" rx="1" fill="var(--paper)" />
      <rect x="17" y="14" width="6" height="19" rx="1" fill="var(--paper)" />
      <rect x="27" y="7" width="6" height="26" rx="1" fill="var(--paper)" />
    </svg>
  );
}

function TargetIcon() {
  return (
    <svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true">
      <circle cx="20" cy="20" r="13" fill="none" stroke="var(--paper)" strokeWidth="1.8" />
      <circle cx="20" cy="20" r="7.5" fill="none" stroke="var(--paper)" strokeWidth="1.8" />
      <circle cx="20" cy="20" r="2.2" fill="var(--paper)" />
    </svg>
  );
}

function GraduationCapIcon() {
  return (
    <svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true">
      <path
        d="M20 9 L36 16 L20 23 L4 16 Z"
        fill="none"
        stroke="var(--paper)"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path
        d="M11 19.5 V27 C11 29.2 15 31 20 31 C25 31 29 29.2 29 27 V19.5"
        fill="none"
        stroke="var(--paper)"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path d="M36 16 V25" fill="none" stroke="var(--paper)" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function PersonIcon() {
  return (
    <svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true">
      <circle cx="20" cy="13" r="6.5" fill="none" stroke="var(--paper)" strokeWidth="1.8" />
      <path
        d="M7 33 C7 25 12.5 21 20 21 C27.5 21 33 25 33 33"
        fill="none"
        stroke="var(--paper)"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

function DocumentIcon() {
  return (
    <svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true">
      <rect x="9" y="5" width="22" height="30" rx="2" fill="none" stroke="var(--paper)" strokeWidth="1.8" />
      <line x1="14" y1="14" x2="26" y2="14" stroke="var(--paper)" strokeWidth="1.6" strokeLinecap="round" />
      <line x1="14" y1="20" x2="26" y2="20" stroke="var(--paper)" strokeWidth="1.6" strokeLinecap="round" />
      <line x1="14" y1="26" x2="22" y2="26" stroke="var(--paper)" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

const HERO_FEATURES = [
  {
    icon: <BarsIcon />,
    title: "Tracks your mastery",
    text: "Knows what you've learned and what to focus on",
  },
  {
    icon: <TargetIcon />,
    title: "Identifies knowledge gaps",
    text: "Finds weak areas in your foundational understanding",
  },
  {
    icon: <GraduationCapIcon />,
    title: "Guides you step by step",
    text: "Provides clear explanations and practice tailored to you",
  },
];

const BUILT_FOR_SUCCESS = [
  { icon: <PersonIcon />, text: "Personalized learning path" },
  { icon: <DocumentIcon />, text: "Step-by-step explanations" },
  { icon: <TargetIcon />, text: "Focused practice and feedback" },
  { icon: <BarsIcon />, text: "Build confidence for exam day" },
];

function ShieldCheckIcon() {
  return (
    <svg viewBox="0 0 40 40" width="36" height="36" aria-hidden="true">
      <path
        d="M20 6 L32 10 V19 C32 27 27 32 20 35 C13 32 8 27 8 19 V10 Z"
        fill="none"
        stroke="var(--paper)"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path
        d="M14 20 L18 24 L27 14"
        fill="none"
        stroke="var(--paper)"
        strokeWidth="1.8"
        strokeLinecap="round"
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
          <Link className="btn" href="#faq">
            FAQ
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
            <>
              <button type="button" className="btn" onClick={() => setShowSignIn(true)}>
                Log in
              </button>
              <button
                type="button"
                className="btn landing-free-banner-btn"
                onClick={() => setShowSignIn(true)}
              >
                Sign up free
              </button>
            </>
          )}
        </MarketingHeader>

        <div className="landing-hero">
          <h1>Your personal tutor for actuarial exams</h1>
          <p className="landing-hero-sub">Personalized guidance that adapts as you learn.</p>

          <div className="landing-hero-features-row">
            {HERO_FEATURES.map((f) => (
              <div className="landing-hero-features-row-item" key={f.title}>
                <span className="landing-hero-features-row-icon">{f.icon}</span>
                <div className="landing-hero-features-row-title">{f.title}</div>
                <p>{f.text}</p>
              </div>
            ))}
          </div>

          <button
            type="button"
            className="btn landing-free-banner-btn landing-hero-cta"
            onClick={() => setShowSignIn(true)}
          >
            Try the tutor free &rarr;
          </button>
          <p className="landing-hero-cta-note">
            Study manuals and formula sheets are free for everyone -- no account required.
          </p>

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

          <div className="landing-built-divider">
            <span />
            <span className="landing-built-label">Built for your success</span>
            <span />
          </div>
          <div className="landing-built-row">
            {BUILT_FOR_SUCCESS.map((item, i) => (
              <div className="landing-built-item" key={i}>
                <span className="landing-hero-features-row-icon landing-built-icon">
                  {item.icon}
                </span>
                <span>{item.text}</span>
              </div>
            ))}
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
            Your tutor does more than answer questions. It continuously tracks
            your proficiency across exam topics, identifies gaps in
            foundational knowledge, and uses what it learns about your
            progress to guide what you should study next.
          </p>
        </div>
      </div>

      <div className="landing-proficiency">
        <h2>Proficiency Dashboard that tracks progress</h2>
        <p>
          Every conversation with the tutor sharpens your proficiency scores, topic by
          topic, so you always know what&apos;s strong and what still needs work.
        </p>
        <div className="preview-window reveal proficiency-preview">
          <div className="proficiency-preview-frame">
            <Image
              src="/proficiencyscreenshot.png"
              alt="Proficiency dashboard showing per-topic mastery scores for Exam P, most topics scored Strong"
              width={1368}
              height={1150}
              className="proficiency-preview-img"
            />
            <div className="proficiency-preview-fade" aria-hidden="true" />
          </div>
        </div>
      </div>

      <div className="landing-guarantee">
        <div className="guarantee-card reveal">
          <span className="guarantee-icon">
            <ShieldCheckIcon />
          </span>
          <div className="guarantee-text">
            <div className="guarantee-title">Our Pass Guarantee</div>
            <p>
              Our goal isn&apos;t just to get you subscribed -- it&apos;s to get you to a
              passing score. If you take the exam and don&apos;t pass, we&apos;ll
              automatically extend your subscription by the number of months you
              originally paid for, so you can keep working toward passing. And once
              you&apos;ve paid for 4 months total and still haven&apos;t passed, continued
              access is free for as long as you need it.
            </p>
            <button
              type="button"
              className="btn landing-free-banner-btn guarantee-btn"
              onClick={() => router.push("/pricing")}
            >
              See pricing &amp; subscribe &rarr;
            </button>
          </div>
        </div>
      </div>

      <div className="landing-faq" id="faq">
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
