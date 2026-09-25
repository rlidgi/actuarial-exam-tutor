"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError, type ClubSponsorshipRequest } from "@/lib/api";

const EMPTY: ClubSponsorshipRequest = {
  name: "",
  email: "",
  university: "",
  event_dates: "",
  human_check: "",
};

// Same modal shell as ambassadors/apply-modal.tsx (backdrop click and
// Escape close it, body scroll locked while open), recolored to the
// landing page's palette via .club-modal.
export function ClubSponsorshipModal({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState<ClubSponsorshipRequest>(EMPTY);
  // Honeypot -- hidden via sr-only, left empty by real visitors. A filled-in
  // value means a bot; the backend accepts it silently without emailing.
  const [website, setWebsite] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    nameRef.current?.focus();
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const set =
    (key: keyof ClubSponsorshipRequest) =>
    (e: { target: { value: string } }) =>
      setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.submitClubSponsorship(
        {
          name: form.name.trim(),
          email: form.email.trim(),
          university: form.university.trim(),
          event_dates: form.event_dates.trim(),
          human_check: form.human_check.trim(),
        },
        website
      );
      setSent(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't send your request. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="amb-modal club-modal my-auto w-full max-w-lg"
        role="dialog"
        aria-modal="true"
        aria-labelledby="club-sponsorship-title"
        onClick={(e) => e.stopPropagation()}
      >
        <button type="button" className="amb-modal-close" aria-label="Close" onClick={onClose}>
          &times;
        </button>
        <h2 id="club-sponsorship-title">Request a Club Sponsorship</h2>

        {sent ? (
          <div className="amb-modal-sent">
            <p>
              Thanks, {form.name.trim()}! We&rsquo;ve received your request and will get back to you
              at <strong>{form.email.trim()}</strong>.
            </p>
            <button type="button" className="amb-btn" onClick={onClose}>
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="amb-form">
            <p className="amb-modal-sub">
              For student actuarial clubs. Tell us about your club&rsquo;s next event.
            </p>
            <label>
              Your name
              <input ref={nameRef} type="text" required maxLength={200} value={form.name} onChange={set("name")} />
            </label>
            <label>
              Your email
              <input type="email" required maxLength={320} value={form.email} onChange={set("email")} />
            </label>
            <label>
              Your college/university
              <input type="text" required maxLength={200} value={form.university} onChange={set("university")} />
            </label>
            <label>
              Upcoming meeting/event date(s)
              <input
                type="text"
                required
                maxLength={500}
                placeholder="e.g. Oct 14 general meeting"
                value={form.event_dates}
                onChange={set("event_dates")}
              />
            </label>
            <label>
              What is 1 plus 2?
              <input
                type="text"
                required
                inputMode="numeric"
                autoComplete="off"
                maxLength={10}
                value={form.human_check}
                onChange={set("human_check")}
              />
            </label>

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

            {error && <p className="amb-form-error">{error}</p>}

            <button type="submit" className="amb-btn" disabled={submitting}>
              {submitting ? "Sending..." : "Submit request"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
