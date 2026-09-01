"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { MarketingHeader } from "@/components/marketing-header";
import { SiteFooter } from "@/components/site-footer";
import { SignInModal } from "@/components/sign-in-modal";

export default function ReferralsContent() {
  const { token } = useAuth();
  const router = useRouter();
  const [showSignIn, setShowSignIn] = useState(false);

  // Signed-in visitors go straight to their referral link on the account
  // page; signed-out visitors get the sign-in modal, same pattern as the
  // rest of the site's "find your way to a gated page" CTAs.
  const handleFindLink = () => {
    if (token) {
      router.push("/account");
    } else {
      setShowSignIn(true);
    }
  };

  return (
    <div className="landing">
      {showSignIn && <SignInModal onClose={() => setShowSignIn(false)} />}

      <MarketingHeader>
        {token ? (
          <Link className="btn" href="/chat">
            Back to Tutor
          </Link>
        ) : (
          <Link className="btn" href="/">
            Home
          </Link>
        )}
      </MarketingHeader>

      <article className="legal-body about-body">
        <h1>Refer a Friend</h1>
        <p>
          Know someone else studying for an actuarial exam? Share your referral link and
          you&apos;ll both come out ahead.
        </p>

        <h2>How it works</h2>
        <ol>
          <li>
            <strong>Get your link.</strong> Every registered user has a personal referral
            link, found on the Referrals page in your account -- click &ldquo;Referrals&rdquo;
            in the tutor&apos;s sidebar.
          </li>
          <li>
            <strong>Share it.</strong> Send it to a classmate, study group, or anyone else
            preparing for Exam P, FM, or FAM.
          </li>
          <li>
            <strong>They save, you earn.</strong> When they subscribe using your link, they
            get 25% off their first month, and you earn $10 toward your own subscription.
            It&apos;s held as a reward balance and applied automatically as an account
            credit right before your next payment is due -- no forms to fill out.
          </li>
        </ol>

        <h2>Prefer cash instead of credit?</h2>
        <p>
          By default, each $10 reward is applied as an account credit toward your own
          subscription right before your next payment comes due. If you&apos;d rather
          receive a reward as cash, email{" "}
          <a href="mailto:support@actuarialexamstutor.com">support@actuarialexamstutor.com</a>{" "}
          <em>before</em> your next payment date and we can arrange a payout by check
          or PayPal instead. Once a reward has been applied as credit, it can&apos;t be
          switched to cash after the fact.
        </p>

        <div style={{ textAlign: "center", margin: "2rem 0 1rem" }}>
          <button type="button" className="btn btn-primary" onClick={handleFindLink}>
            Find your referral link &rarr;
          </button>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
