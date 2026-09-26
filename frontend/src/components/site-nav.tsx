"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { MarketingHeader } from "./marketing-header";

// Main site nav (landing and pricing pages). Render it inside a
// .landing-hero-band wrapper -- that's what gives it the white docked bar
// on desktop and the hamburger menu at 1024px and below (see globals.css).
// FAQ / Actuarial Clubs are sections of the landing page, so off it they
// link back there.
export function SiteNav({ onSignIn }: { onSignIn: () => void }) {
  const { token, logout } = useAuth();
  const onHome = usePathname() === "/";
  const section = (id: string) => (onHome ? `#${id}` : `/#${id}`);

  return (
    <MarketingHeader mobileMenu>
      <Link className="btn" href="/about">
        About
      </Link>
      <Link className="btn" href="/pricing">
        Pricing
      </Link>
      <Link className="btn" href={section("faq")}>
        FAQ
      </Link>
      <Link className="btn" href={section("clubs")}>
        Actuarial Clubs
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
          <button type="button" className="btn landing-login-btn" onClick={onSignIn}>
            Log in
          </button>
          <button type="button" className="btn btn-primary" onClick={onSignIn}>
            Sign up free
          </button>
        </>
      )}
    </MarketingHeader>
  );
}
