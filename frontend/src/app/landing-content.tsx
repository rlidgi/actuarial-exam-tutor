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
  { text: "Σ", left: "3%", top: "17%", fontSize: "3.8rem", delay: "0s" },
  { text: "σ²", left: "12%", top: "24%", fontSize: "2.8rem", delay: "3s" },
  { text: "E[X]", left: "4%", top: "40%", fontSize: "2.3rem", delay: "1.2s" },
  { text: "P(A|B)", left: "3%", top: "59%", fontSize: "2rem", delay: "4.5s" },
  { text: "∫", left: "89%", top: "12%", fontSize: "4.5rem", delay: "1.5s" },
  { text: "Aₓ", left: "94%", top: "27%", fontSize: "2.6rem", delay: "1s" },
  { text: "μ", left: "86%", top: "34%", fontSize: "3.1rem", delay: "4s" },
  { text: "∞", left: "92%", top: "43%", fontSize: "3.4rem", delay: "2.8s" },
  { text: "Var(X)", left: "92%", top: "66%", fontSize: "1.8rem", delay: "2s" },
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

function BarsIcon() {
  return (
    <svg viewBox="0 0 40 40" width="40" height="40" aria-hidden="true">
      <rect x="6" y="21" width="7" height="13" rx="1.5" fill="currentColor" />
      <rect x="16.5" y="13" width="7" height="21" rx="1.5" fill="currentColor" />
      <rect x="27" y="5" width="7" height="29" rx="1.5" fill="currentColor" />
    </svg>
  );
}

function TargetIcon() {
  return (
    <svg viewBox="0 0 40 40" width="40" height="40" aria-hidden="true">
      <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M31.16 17.21 A14 14 0 1 1 22.33 8.69" />
        <path d="M25.99 19.09 A8.5 8.5 0 1 1 20.63 13.92" />
        <circle cx="18" cy="22" r="3" />
        <path d="M18 22 L32 6" />
      </g>
      <path d="M29 9 V5 L32 2 V6 H36 L33 9 Z" fill="currentColor" />
    </svg>
  );
}

function GraduationCapIcon() {
  return (
    <svg viewBox="0 0 40 40" width="40" height="40" aria-hidden="true">
      <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 7 L37 15 L20 23 L3 15 Z" />
        <path d="M10 19 V29 C15 34 25 34 30 29 V19 M36 16 V28" />
      </g>
    </svg>
  );
}

function PersonIcon() {
  return (
    <svg viewBox="0 0 40 40" width="40" height="40" aria-hidden="true">
      <circle cx="20" cy="11" r="7" fill="none" stroke="currentColor" strokeWidth="2" />
      <path
        d="M6 35 V31 C6 23 12 20 20 20 C28 20 34 23 34 31 V35 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function DocumentIcon() {
  return (
    <svg viewBox="0 0 40 40" width="40" height="40" aria-hidden="true">
      <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 4 H23 L32 13 V36 H9 Z M23 4 V13 H32" />
        <path d="M14 19 H26 M14 24 H26 M14 29 H26" />
      </g>
    </svg>
  );
}

// Same blue/gold/green triad as EXAMS' own colors (var(--sky)/var(--gold)/
// var(--ink)), reapplied here via these classes so the two feature rows
// reinforce the same P/FM/FAM color language instead of introducing new
// colors of their own.
const HERO_FEATURES = [
  {
    icon: <BarsIcon />,
    title: "Tracks your mastery",
    text: "Knows what you've learned and what to focus on",
    colorClass: "color-sky",
  },
  {
    icon: <TargetIcon />,
    title: "Identifies knowledge gaps",
    text: "Finds weak areas in your foundational understanding",
    colorClass: "color-gold",
  },
  {
    icon: <GraduationCapIcon />,
    title: "Guides you step by step",
    text: "Provides clear explanations and practice tailored to you",
    colorClass: "color-green",
  },
];

const BUILT_FOR_SUCCESS = [
  { icon: <PersonIcon />, text: "Personalized learning path", colorClass: "color-sky" },
  { icon: <DocumentIcon />, text: "Step-by-step explanations", colorClass: "color-gold" },
  { icon: <TargetIcon />, text: "Focused practice and feedback", colorClass: "color-green" },
  { icon: <BarsIcon />, text: "Build confidence for exam day", colorClass: "color-sky" },
];

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
  // sheet, instead of dropping them straight into sign-in. FAM's overview
  // now lives at examfam.com instead of /exams/FAM (see next.config.ts's
  // redirect for anyone hitting the old URL directly) -- going straight
  // there avoids the extra redirect hop for this button specifically.
  const handleExamClick = (code: string) => {
    if (code === "FAM") {
      // False positive, same as pricing-content.tsx's handleSubscribe/
      // handleManageSubscription -- only ever runs in a click handler, not
      // a mutation during render.
      // eslint-disable-next-line react-hooks/immutability
      window.location.href = "https://examfam.com";
      return;
    }
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
        <MarketingHeader mobileMenu>
          <Link className="btn" href="/about">
            About
          </Link>
          <Link className="btn" href="/pricing">
            Pricing
          </Link>
          <Link className="btn" href="#faq">
            FAQ
          </Link>
          <Link className="btn" href="/ambassadors">
            Campus Rep Program
          </Link>
          <Link className="btn" href="/referrals">
            Referrals
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
              <button
                type="button"
                className="btn landing-login-btn"
                onClick={() => setShowSignIn(true)}
              >
                Log in
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setShowSignIn(true)}
              >
                Sign up free
              </button>
            </>
          )}
        </MarketingHeader>

        <div className="landing-hero">
          <h1>
            Your personal tutor{" "}
            <span>for actuarial exams</span>
          </h1>
          <p className="landing-hero-sub">
            Personalized guidance that adapts as you learn.
          </p>
          <div className="landing-hero-features-row">
            {HERO_FEATURES.map((feature) => (
              <div className="landing-hero-features-row-item" key={feature.title}>
                <span className={`landing-hero-features-row-icon ${feature.colorClass}`}>
                  {feature.icon}
                </span>
                <div>
                  <h2 className="landing-hero-features-row-title">{feature.title}</h2>
                  <p>{feature.text}</p>
                </div>
              </div>
            ))}
          </div>
          <button
            type="button"
            className="btn btn-primary landing-hero-cta"
            onClick={() => token ? router.push("/chat") : setShowSignIn(true)}
          >
            Try the tutor free <span aria-hidden="true">&rarr;</span>
          </button>
          <p className="landing-hero-cta-note">
            Study manuals and formula sheets are free for everyone — no account required.
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
            <span className="landing-built-label">Built for your success</span>
          </div>
          <div className="landing-built-row">
            {BUILT_FOR_SUCCESS.map((item) => (
              <div className="landing-built-item" key={item.text}>
                <span className={`landing-built-icon ${item.colorClass}`}>{item.icon}</span>
                <span>{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="landing-community">
        <h2>Join a growing community of actuarial students</h2>
        <p>Smarter study. Stronger results.</p>
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
            <Image
              src="/pass-guarantee-icon.png"
              alt=""
              width={68}
              height={68}
            />
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
