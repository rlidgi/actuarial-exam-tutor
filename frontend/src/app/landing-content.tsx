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
  const reason = searchParams.get("reason");

  return (
    <div className="banner warn pricing-notice">
      {reason || "Sign-in didn't go through -- try again."}
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
        <h1>Your personal tutor for actuarial exams</h1>
        <p
          className="landing-hero-sub"
          style={{ fontStyle: "italic", fontSize: "20px", color: "rgba(237, 239, 232, 0.78)" }}
        >
          Study smarter for P, FM, and FAM with an AI tutor that explains concepts, works through
          problems, and helps when you get stuck.
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
          <Image
            className="feature-illustration"
            src="/books-v3.webp"
            alt="An icon of a stack of books with a magnifying glass, representing textbook-grounded answers"
            width={300}
            height={200}
          />
          <div className="feature-title">Grounded in your textbooks</div>
          <p>
            Every response is grounded in the exact SOA/CAS specified textbooks for that exam.
            When appropriate, cites text directly and provides page number and textbook name for
            further study.
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
            Attach an image or paste a screenshot of a problem. Instead of simply giving you the
            answer, the tutor works through the problem with you step by step, helping you
            understand how to solve it.
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
            The actuarial tutor adapts to each student&apos;s unique needs, much like a human
            tutor. It continuously tracks proficiency, strengthens foundational knowledge where
            needed, and guides students step by step toward mastery.
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
