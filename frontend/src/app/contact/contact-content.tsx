"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";
import { MarketingHeader } from "@/components/marketing-header";
import { SiteFooter } from "@/components/site-footer";

export default function ContactContent() {
  const { token } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  // Honeypot -- hidden from real visitors via the sr-only class below, left
  // empty by anyone using an actual browser. A filled-in value means a bot.
  const [website, setWebsite] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.submitContact(name.trim(), email.trim(), message.trim(), website);
      setSent(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't send your message. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="landing">
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

      <article className="legal-body">
        <h1>Contact Us</h1>
        <p>
          Questions, feedback, or anything else on your mind -- send us a message and we&rsquo;ll
          get back to you.
        </p>

        {sent ? (
          <p className="mt-4 text-sm text-ink">
            Thanks for reaching out! We&rsquo;ll get back to you at <strong>{email}</strong> soon.
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="mt-4 flex max-w-md flex-col gap-3">
            <label className="flex flex-col gap-1 text-sm text-pencil">
              Name
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="rounded-md border border-rule bg-transparent px-3 py-2 text-ink"
              />
            </label>

            <label className="flex flex-col gap-1 text-sm text-pencil">
              Email
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-md border border-rule bg-transparent px-3 py-2 text-ink"
              />
            </label>

            <label className="flex flex-col gap-1 text-sm text-pencil">
              Message
              <textarea
                required
                rows={5}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="rounded-md border border-rule bg-transparent px-3 py-2 text-ink"
              />
            </label>

            {/* Honeypot: real users never see or fill this in. */}
            <label className="sr-only" aria-hidden="true">
              Leave this field blank
              <input
                type="text"
                tabIndex={-1}
                autoComplete="off"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
              />
            </label>

            {error && <p className="text-sm text-redink">{error}</p>}

            <button
              type="submit"
              disabled={submitting}
              className="self-start rounded-md bg-ledger px-4 py-2 text-sm font-semibold text-paper hover:bg-ledger-bright disabled:opacity-50"
            >
              {submitting ? "Sending..." : "Send message"}
            </button>
          </form>
        )}
      </article>

      <SiteFooter />
    </div>
  );
}
