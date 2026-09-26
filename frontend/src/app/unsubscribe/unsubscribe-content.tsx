"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { MarketingHeader } from "@/components/marketing-header";
import { SiteFooter } from "@/components/site-footer";

type Status = "working" | "done" | "error";

// Landing page for the unsubscribe link in the feedback-request email
// (backend feedback_request_service.py). Unsubscribes on load -- the signed
// token in the link is the proof of identity, no sign-in needed.
export default function UnsubscribeContent() {
  const token = useSearchParams().get("token") ?? "";
  const [status, setStatus] = useState<Status>("working");

  useEffect(() => {
    let ignore = false;
    const run = token
      ? api.unsubscribeEmails(token).then(() => "done" as const)
      : Promise.resolve("error" as const);
    run
      .catch(() => "error" as const)
      .then((result) => {
        if (!ignore) setStatus(result);
      });
    return () => {
      ignore = true;
    };
  }, [token]);

  return (
    <div className="landing">
      <MarketingHeader>
        <Link className="btn" href="/">
          Home
        </Link>
      </MarketingHeader>

      <article className="legal-body">
        <h1>Email preferences</h1>
        {status === "working" && <p>Updating your preferences&hellip;</p>}
        {status === "done" && (
          <p>
            You&rsquo;ve been unsubscribed. You won&rsquo;t receive feedback request emails from
            Actuarial Exams Tutor anymore. Account emails, like sign-in links, still come through.
          </p>
        )}
        {status === "error" && (
          <p>
            This unsubscribe link isn&rsquo;t valid. If you&rsquo;d like to stop receiving emails,
            reply to one of our emails or{" "}
            <Link href="/contact">contact us</Link> and we&rsquo;ll take care of it.
          </p>
        )}
      </article>

      <SiteFooter />
    </div>
  );
}
