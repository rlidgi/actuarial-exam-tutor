"use client";

import { useState, type ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { MarketingHeader } from "@/components/marketing-header";
import { SiteFooter } from "@/components/site-footer";
import { SignInModal } from "@/components/sign-in-modal";
import { ApplyModal } from "./apply-modal";

const svgProps = {
  width: 30,
  height: 30,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

const BENEFITS: { title: string; text: string; color: string; icon: ReactNode }[] = [
  {
    title: "Lifetime Access",
    text: "Receive lifetime access to AET for your next preliminary exam.",
    color: "blue",
    icon: (
      <svg {...svgProps}>
        <path d="M2 9l10-5 10 5-10 5z" />
        <path d="M6 11v5c0 1.5 2.7 3 6 3s6-1.5 6-3v-5" />
        <path d="M22 9v5" />
      </svg>
    ),
  },
  {
    title: "Earn $5 Per Student",
    text: "For every student at your school who subscribes using your school's unique URL, you'll receive $5.",
    color: "green",
    icon: (
      <svg {...svgProps}>
        <path d="M12 3v18" />
        <path d="M16.5 7.5c-.8-1.2-2.4-2-4.5-2-2.6 0-4.5 1.3-4.5 3.2 0 4.3 9 2.5 9 6.8 0 1.9-1.9 3.2-4.5 3.2-2.1 0-3.8-.8-4.6-2.1" />
      </svg>
    ),
  },
  {
    title: "Make an Impact",
    text: "Help fellow actuarial students succeed and build a stronger actuarial community on your campus, while gaining leadership experience that stands out on your resume.",
    color: "purple",
    icon: (
      <svg {...svgProps}>
        <circle cx="12" cy="8" r="3" />
        <circle cx="5" cy="10" r="2.2" />
        <circle cx="19" cy="10" r="2.2" />
        <path d="M6.5 19c0-3 2.5-5 5.5-5s5.5 2 5.5 5" />
        <path d="M1.5 18c0-2.2 1.5-3.7 3.5-3.7M22.5 18c0-2.2-1.5-3.7-3.5-3.7" />
      </svg>
    ),
  },
];

const RESPONSIBILITIES: { title: string; text: string; color: string; icon: ReactNode }[] = [
  {
    title: "Share the Discount",
    text: "Communicate the 15% AET discount available to all students at your university.",
    color: "blue",
    icon: (
      <svg {...svgProps}>
        <path d="M3 10v4h3l7 4V6L6 10z" />
        <path d="M6 14l1.5 5h2.5l-1.3-4.3" />
        <path d="M17 9.5a3.5 3.5 0 0 1 0 5M19.5 7a7 7 0 0 1 0 10" />
      </svg>
    ),
  },
  {
    title: "Distribute a Flyer",
    text: "Post and distribute an AET flyer through appropriate campus and student channels.",
    color: "green",
    icon: (
      <svg {...svgProps}>
        <path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8z" />
        <path d="M14 3v5h5" />
        <path d="M8.5 12.5h7M8.5 16h7" />
      </svg>
    ),
  },
  {
    title: "Promote on Club Website",
    text: "Advocate for AET's inclusion on the Actuarial Club website as an exam-preparation resource.",
    color: "purple",
    icon: (
      <svg {...svgProps}>
        <rect x="3" y="4" width="18" height="12" rx="1.5" />
        <path d="M12 16v4M8 20h8" />
      </svg>
    ),
  },
  {
    title: "Find Future Ambassadors",
    text: "At the end of your term, identify three potential candidates to serve as the next AET Campus Ambassador.",
    color: "gold",
    icon: (
      <svg {...svgProps}>
        <circle cx="12" cy="8" r="2.6" />
        <circle cx="5" cy="9" r="2.2" />
        <circle cx="19" cy="9" r="2.2" />
        <path d="M7.5 19c0-2.7 2-4.6 4.5-4.6s4.5 1.9 4.5 4.6" />
        <path d="M1.5 18c0-2.2 1.5-3.7 3.5-3.7M22.5 18c0-2.2-1.5-3.7-3.5-3.7" />
      </svg>
    ),
  },
];

const FAQS = [
  {
    q: "Who can apply?",
    a: "We're looking for motivated actuarial students who are active in their campus community.",
  },
  {
    q: "How long is the term?",
    a: "Terms typically run for one academic year, with the opportunity to renew.",
  },
  {
    q: "How do students get the discount?",
    a: "Each school has a dedicated URL that provides 15% off all AET products for students at your university.",
  },
  {
    q: "How are referrals tracked?",
    a: "Subscriptions are tracked automatically through your school's unique URL.",
  },
];

function Arrow() {
  return <span aria-hidden="true">&rarr;</span>;
}

export default function AmbassadorsContent() {
  const { token } = useAuth();
  const [showSignIn, setShowSignIn] = useState(false);
  const [showApply, setShowApply] = useState(false);

  return (
    <div className="landing amb-page">
      {showSignIn && <SignInModal onClose={() => setShowSignIn(false)} />}
      {showApply && <ApplyModal onClose={() => setShowApply(false)} />}

      <MarketingHeader mobileMenu>
        <Link className="btn" href="/">
          Home
        </Link>
        <Link className="btn" href="/pricing">
          Pricing
        </Link>
        <Link className="btn" href="/about">
          About
        </Link>
        {token ? (
          <Link className="btn btn-primary" href="/chat">
            Go to Tutor
          </Link>
        ) : (
          <>
            <button
              type="button"
              className="btn landing-login-btn"
              onClick={() => setShowSignIn(true)}
            >
              Log in
            </button>
            <button type="button" className="btn btn-primary" onClick={() => setShowSignIn(true)}>
              Sign up free
            </button>
          </>
        )}
      </MarketingHeader>

      <section className="amb-hero">
        <div className="amb-hero-text">
          <p className="amb-eyebrow">Campus Ambassador Program</p>
          <h1>Make a difference on your campus</h1>
          <p>
            Help fellow actuarial students succeed while gaining valuable experience and
            rewards. Join the Actuarial Exams Tutor Campus Ambassador Program!
          </p>
          <button type="button" className="amb-btn" onClick={() => setShowApply(true)}>
            Apply to Become an Ambassador <Arrow />
          </button>
        </div>
      </section>

      <section className="amb-section">
        <h2>Ambassador Benefits</h2>
        <p className="amb-section-sub">As an AET Campus Ambassador, you&apos;ll receive:</p>
        <div className="amb-benefits">
          {BENEFITS.map((b) => (
            <div key={b.title} className={`amb-benefit amb-tint-${b.color}`}>
              <span className={`amb-icon-solid amb-${b.color}`}>{b.icon}</span>
              <h3>{b.title}</h3>
              <p>{b.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="amb-section">
        <h2>Ambassador Responsibilities</h2>
        <p className="amb-section-sub">
          The time commitment is flexible and fits easily alongside your studies.
        </p>
        <div className="amb-duties">
          {RESPONSIBILITIES.map((r) => (
            <div key={r.title} className="amb-duty">
              <span className={`amb-icon-soft amb-${r.color}`}>{r.icon}</span>
              <div>
                <h3>{r.title}</h3>
                <p>{r.text}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="amb-community">
        <div className="amb-community-text">
          <h2>
            Support Your Peers.
            <br />
            Strengthen Your Community.
          </h2>
          <p>
            As a campus ambassador, you&apos;ll help more students access high-quality
            actuarial exam preparation, while earning rewards and building leadership
            experience.
          </p>
          <button type="button" className="amb-btn" onClick={() => setShowApply(true)}>
            Apply Now <Arrow />
          </button>
        </div>
        <Image
          className="amb-community-art"
          src="/ambassador-community.png"
          alt="Three students under a graduation cap: Better preparation. A stronger actuarial community."
          width={1536}
          height={1024}
        />
      </section>

      <section className="amb-section">
        <h2 className="amb-faq-title">Frequently Asked Questions</h2>
        <div className="amb-faq">
          {FAQS.map((f) => (
            <details key={f.q} className="amb-faq-item">
              <summary>{f.q}</summary>
              <p>{f.a}</p>
            </details>
          ))}
        </div>
      </section>


      <SiteFooter />
    </div>
  );
}
