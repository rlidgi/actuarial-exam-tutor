"use client";

import { useState, type ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";

export function MarketingHeader({
  children,
  mobileMenu = false,
}: {
  children: ReactNode;
  /** Landing page only (see landing-content.tsx) -- collapses the links
   * into a hamburger toggle below the 800px breakpoint. Every other page
   * using this header (About, Pricing, Contact, exam overview, Referrals)
   * leaves this off and renders exactly as before: links always inline,
   * no toggle button, unaffected by the mobile CSS below. */
  mobileMenu?: boolean;
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className={`landing-nav${mobileMenu ? " landing-nav-hamburger" : ""}`}>
      <Link href="/" className="wordmark-group">
        <Image src="/logo-mark.png" alt="" width={110} height={56} className="wordmark-mark" />
        <span className="wordmark-divider" />
        <Image
          src="/logo-text.png"
          alt="Actuarial Exams Tutor"
          width={220}
          height={26}
          className="wordmark-text"
        />
      </Link>
      {mobileMenu && (
        <button
          type="button"
          className="landing-nav-toggle"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((prev) => !prev)}
        >
          <span />
          <span />
          <span />
        </button>
      )}
      <div className={`landing-nav-links${menuOpen ? " landing-nav-links-open" : ""}`}>
        {children}
      </div>
    </header>
  );
}
