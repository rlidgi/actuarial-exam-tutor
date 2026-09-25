"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError, type AmbassadorApplication } from "@/lib/api";

const EMPTY: AmbassadorApplication = {
  name: "",
  email: "",
  school: "",
  graduation_year: "",
  actuarial_club: "",
  exams: "",
  message: "",
};

// Same modal shell as components/sign-in-modal.tsx (backdrop click and
// Escape close it, body scroll locked while open), styled with this page's
// .amb-* palette.
export function ApplyModal({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState<AmbassadorApplication>(EMPTY);
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
    (key: keyof AmbassadorApplication) =>
    (e: { target: { value: string } }) =>
      setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.submitAmbassadorApplication(
        {
          ...form,
          name: form.name.trim(),
          email: form.email.trim(),
          school: form.school.trim(),
          graduation_year: form.graduation_year.trim(),
          exams: form.exams.trim(),
          message: form.message.trim(),
        },
        website
      );
      setSent(true);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Couldn't send your application. Try again."
      );
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
        className="amb-modal my-auto w-full max-w-lg"
        role="dialog"
        aria-modal="true"
        aria-labelledby="amb-apply-title"
        onClick={(e) => e.stopPropagation()}
      >
        <button type="button" className="amb-modal-close" aria-label="Close" onClick={onClose}>
          &times;
        </button>
        <h2 id="amb-apply-title">Apply to Become an Ambassador</h2>

        {sent ? (
          <div className="amb-modal-sent">
            <p>
              Thanks, {form.name.trim()}! Your application is in. We&rsquo;ll get back to you at{" "}
              <strong>{form.email.trim()}</strong>.
            </p>
            <button type="button" className="amb-btn" onClick={onClose}>
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="amb-form">
            <p className="amb-modal-sub">
              Tell us a bit about yourself and we&rsquo;ll be in touch.
            </p>
            <label>
              Full name
              <input ref={nameRef} type="text" required maxLength={200} value={form.name} onChange={set("name")} />
            </label>
            <label>
              Email
              <input type="email" required maxLength={320} value={form.email} onChange={set("email")} />
            </label>
            <label>
              School
              <input type="text" required maxLength={200} value={form.school} onChange={set("school")} />
            </label>
            <div className="amb-form-row">
              <label>
                <span>
                  Graduation year <span className="amb-optional">(optional)</span>
                </span>
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={10}
                  placeholder="e.g. 2028"
                  value={form.graduation_year}
                  onChange={set("graduation_year")}
                />
              </label>
              <label>
                <span>
                  In your actuarial club? <span className="amb-optional">(optional)</span>
                </span>
                <select value={form.actuarial_club} onChange={set("actuarial_club")}>
                  <option value="">Select&hellip;</option>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                  <option value="no_club">My school doesn&rsquo;t have one</option>
                </select>
              </label>
            </div>
            <label>
              Have you taken any exams? Which exam are you currently studying for?
              <textarea
                required
                rows={2}
                maxLength={1000}
                placeholder="e.g. Passed P, currently studying for FM"
                value={form.exams}
                onChange={set("exams")}
              />
            </label>
            <label>
              Why do you want to be an ambassador?
              <textarea required rows={4} maxLength={5000} value={form.message} onChange={set("message")} />
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
              {submitting ? "Sending..." : "Submit application"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
