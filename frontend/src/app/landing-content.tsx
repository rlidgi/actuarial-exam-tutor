"use client";

import { Suspense, useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { FAQ_ITEMS } from "@/lib/faq-data";
import { useReveal } from "@/lib/use-reveal";
import { SiteNav } from "@/components/site-nav";
import { SiteFooter } from "@/components/site-footer";
import { SignInModal } from "@/components/sign-in-modal";
import { ClubSponsorshipModal } from "./club-sponsorship-modal";
import { EXAM_ICONS } from "@/components/exam-icons";

const EXAMS = [
  {
    code: "P",
    name: "Probability",
    color: "#1f6fe5",
    text: "Combinatorics, conditional probability and Bayes' theorem, and univariate and multivariate distributions: the foundation for every later exam.",
  },
  {
    code: "FM",
    name: "Financial Mathematics",
    color: "#12a37f",
    text: "Time value of money, annuities, loans, bonds, and interest rate risk, worked through step by step.",
  },
  {
    code: "FAM",
    name: "Fundamentals of Actuarial Mathematics",
    color: "#8250df",
    text: "Survival models, life tables, and valuing life insurance and annuities, grounded in the SOA-specified textbooks.",
  },
];

const HERO_POINTS = [
  {
    title: "Grounded in SOA/CAS textbooks",
    text: "Answers include textbook citations when appropriate.",
  },
  {
    title: "Tracks your progress",
    text: "Identifies gaps and focuses on what you need to improve.",
  },
  {
    title: "Personalized to your strengths and weaknesses",
    text: "Adapts to your learning style and goals.",
  },
];

const highlightIconProps = {
  width: 34,
  height: 34,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

const HIGHLIGHTS = [
  {
    title: "Textbook-Grounded",
    text: "Answers are based on the exact SOA/CAS-specified textbooks, with citations when appropriate.",
    colorClass: "landing-highlight-blue",
    icon: (
      <svg {...highlightIconProps}>
        <path d="M12 6.5C10 5 7 4.5 3.5 5v13c3.5-.5 6.5 0 8.5 1.5 2-1.5 5-2 8.5-1.5V5C17 4.5 14 5 12 6.5Z" />
        <path d="M12 6.5v13" />
      </svg>
    ),
  },
  {
    title: "Personalized Learning",
    text: "Tracks your proficiency, identifies gaps, and adapts to your learning style.",
    colorClass: "landing-highlight-green",
    icon: (
      <svg {...highlightIconProps}>
        <path d="M5 20v-5M10 20v-8M15 20v-6M20 20V9" />
        <path d="M4 11l5-4 4 3 7-6M16 4h4v4" />
      </svg>
    ),
  },
  {
    title: "Step-by-Step Support",
    text: "Get clear, detailed explanations and follow-up help whenever you need it.",
    colorClass: "landing-highlight-purple",
    icon: (
      <svg {...highlightIconProps}>
        <circle cx="12" cy="12" r="8.5" />
        <circle cx="12" cy="12" r="4.5" />
        <path d="M12 12l7-7M16 5h3v3" />
      </svg>
    ),
  },
  {
    title: "Study Smarter",
    text: "Focus on what matters and make the most of your study time.",
    colorClass: "landing-highlight-gold",
    icon: (
      <svg {...highlightIconProps}>
        <circle cx="12" cy="12" r="8.5" />
        <path d="M12 7.5V12l3 2" />
      </svg>
    ),
  },
];

const CLUB_PERKS = [
  {
    text: "Reimbursement for food & drinks for a group event",
    colorClass: "color-gold",
    icon: (
      <svg viewBox="0 0 40 40" width="30" height="30" aria-hidden="true">
        <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M8 16 H26 V26 C26 31 22 34 17 34 C12 34 8 31 8 26 Z" />
          <path d="M26 19 H29 C31.5 19 33 20.5 33 22.5 C33 24.5 31.5 26 29 26 H26" />
          <path d="M12 6 C12 9 14 9 14 12 M18 6 C18 9 20 9 20 12" />
        </g>
      </svg>
    ),
  },
  {
    text: "A care package full of AET shirts, pens, pencils, stickers, etc...",
    colorClass: "color-sky",
    icon: (
      <svg viewBox="0 0 40 40" width="30" height="30" aria-hidden="true">
        <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M5 13 H35 V19 H5 Z" />
          <path d="M8 19 V35 H32 V19 M20 13 V35" />
          <path d="M20 13 C17 13 12 12 12 8.5 C12 5 17 6 20 13 C23 6 28 5 28 8.5 C28 12 23 13 20 13" />
        </g>
      </svg>
    ),
  },
  {
    text: "One free 1 month subscription to an AET Prelim course to give away during the event",
    colorClass: "color-green",
    icon: (
      <svg viewBox="0 0 40 40" width="30" height="30" aria-hidden="true">
        <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 12 H36 V17 C33.5 17 32 18.5 32 20.5 C32 22.5 33.5 24 36 24 V29 H4 V24 C6.5 24 8 22.5 8 20.5 C8 18.5 6.5 17 4 17 Z" />
          <path d="M26 12 V29" strokeDasharray="2 3" />
          <path d="M16 16.5 L17.4 19.3 L20.5 19.7 L18.2 21.9 L18.8 25 L16 23.5 L13.2 25 L13.8 21.9 L11.5 19.7 L14.6 19.3 Z" />
        </g>
      </svg>
    ),
  },
  {
    text: "An AET rep can visit virtually to answer questions & demo the AET platform",
    colorClass: "color-sky",
    icon: (
      <svg viewBox="0 0 40 40" width="30" height="30" aria-hidden="true">
        <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="4" y="7" width="32" height="21" rx="2" />
          <path d="M14 34 H26 M20 28 V34" />
          <circle cx="20" cy="15" r="3.5" />
          <path d="M13.5 24.5 C14.5 21.5 17 20 20 20 C23 20 25.5 21.5 26.5 24.5" />
        </g>
      </svg>
    ),
  },
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

const REDESIGN_FLASH_KEY = "aet-redesign-bar-closed";

// "We redesigned" bar across the very top of the page, above the nav. Stays
// until closed; closing is remembered in localStorage (same storage the
// chat/exam pickers already use). Visibility lives in LandingContent, since
// the page root needs a class to shift the docked desktop nav below it.
function RedesignFlash({ onClose }: { onClose: () => void }) {
  return (
    <div className="redesign-flash" role="status">
      <span>
        <span aria-hidden="true">&#10024;</span> We&apos;ve recently redesigned our site.
        Take a look around!
      </span>
      <button type="button" aria-label="Close" onClick={onClose}>
        &times;
      </button>
    </div>
  );
}

export default function LandingContent() {
  const { token } = useAuth();
  const router = useRouter();
  const [showSignIn, setShowSignIn] = useState(false);
  const [showClubForm, setShowClubForm] = useState(false);
  // Starts hidden so the server render and first client render match; the
  // stored "closed" flag can only be read once mounted.
  const [showFlash, setShowFlash] = useState(false);
  useEffect(() => {
    let closed = false;
    try {
      closed = window.localStorage.getItem(REDESIGN_FLASH_KEY) === "1";
    } catch {
      // Storage blocked (private mode etc.) -- just show it this visit.
    }
    if (closed) return;
    const show = window.setTimeout(() => setShowFlash(true), 0);
    return () => window.clearTimeout(show);
  }, []);
  const closeFlash = () => {
    setShowFlash(false);
    try {
      window.localStorage.setItem(REDESIGN_FLASH_KEY, "1");
    } catch {
      // ignore
    }
  };
  useReveal();

  // Each exam card links to that exam's overview page, which describes the
  // free and paid resources on offer and links to the free study
  // manual/formula sheet, instead of dropping visitors straight into
  // sign-in. FAM's overview now lives at examfam.com instead of /exams/FAM
  // (see next.config.ts's redirect for anyone hitting the old URL
  // directly) -- linking straight there avoids the extra redirect hop.
  const examHref = (code: string) =>
    code === "FAM" ? "https://examfam.com" : `/exams/${code}`;

  return (
    <div className={`landing${showFlash ? " landing-has-flash" : ""}`}>
      {showFlash && <RedesignFlash onClose={closeFlash} />}
      <Suspense fallback={null}>
        <SignInErrorBanner />
      </Suspense>

      {showSignIn && <SignInModal onClose={() => setShowSignIn(false)} />}
      {showClubForm && <ClubSponsorshipModal onClose={() => setShowClubForm(false)} />}

      <div className="landing-hero-band">
        <SiteNav onSignIn={() => setShowSignIn(true)} />

        <section className="landing-hero">
          <div className="landing-hero-copy">
            <h1>Master Actuarial Exams with Your AI Tutor</h1>
            <p className="landing-hero-sub">
              Get step-by-step explanations, personalized guidance, and the confidence to pass.
            </p>
            <ul className="landing-hero-points">
              {HERO_POINTS.map((point) => (
                <li key={point.title}>
                  <span className="landing-hero-check" aria-hidden="true">
                    <svg viewBox="0 0 24 24" width="16" height="16">
                      <path
                        d="M5 12.5l4.5 4.5L19 7.5"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </span>
                  <div>
                    <strong>{point.title}</strong>
                    <span>{point.text}</span>
                  </div>
                </li>
              ))}
            </ul>
            <button
              type="button"
              className="landing-hero-cta"
              onClick={() => (token ? router.push("/chat") : setShowSignIn(true))}
            >
              {token ? "Go to Tutor" : "Try the tutor free"} <span aria-hidden="true">&rarr;</span>
            </button>
            <p className="landing-hero-note">
              Study manuals and formula sheets are free for everyone, no account required.
            </p>
          </div>
        </section>
      </div>

      <div className="landing-highlights">
        {HIGHLIGHTS.map((item) => (
          <div className="landing-highlight" key={item.title}>
            <span className={`landing-highlight-icon ${item.colorClass}`}>{item.icon}</span>
            <h2>{item.title}</h2>
            <p>{item.text}</p>
          </div>
        ))}
      </div>

      <section className="landing-exams">
        <h2>Prepare for Your Next Exam</h2>
        <p className="landing-exams-sub">Currently available for the preliminary actuarial exams.</p>
        <div className="landing-exams-grid">
          {EXAMS.map((e) => (
            <Link
              key={e.code}
              href={examHref(e.code)}
              className="landing-exam-card"
              style={{ "--exam-color": e.color } as React.CSSProperties}
            >
              <span className="landing-exam-badge">{e.code}</span>
              <div className="landing-exam-body">
                <h3>Exam {e.code}</h3>
                <p className="landing-exam-name">{e.name}</p>
                <p>{e.text}</p>
                {/* Phones only (see globals.css) -- on desktop the whole
                    card is the obvious click target. */}
                <span className="landing-exam-link">
                  Learn more <span aria-hidden="true">&rarr;</span>
                </span>
              </div>
              <span className="landing-exam-art" aria-hidden="true">
                {EXAM_ICONS[e.code]?.(e.color)}
              </span>
            </Link>
          ))}
        </div>
      </section>

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
              Our goal isn&apos;t just to get you subscribed, it&apos;s to get you to a
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

      <div className="landing-clubs" id="clubs">
        <p className="landing-clubs-eyebrow">Exclusively for Student Actuarial Clubs</p>
        <h2>Actuarial Club Sponsorships</h2>
        <div className="landing-clubs-grid">
          {CLUB_PERKS.map((perk) => (
            <div className="landing-clubs-item reveal" key={perk.text}>
              <span className={`landing-clubs-icon ${perk.colorClass}`}>{perk.icon}</span>
              <p>{perk.text}</p>
            </div>
          ))}
        </div>
        <button
          type="button"
          className="btn btn-primary landing-clubs-btn"
          onClick={() => setShowClubForm(true)}
        >
          Request a sponsorship &rarr;
        </button>
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
