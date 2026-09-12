"use client";

import { useEffect, useState } from "react";

const STORAGE_PREFIX = "dismissed-notice:";

// Generic one-off announcement banner (e.g. "we fixed a rendering bug,
// sorry about that") -- `id` keys its dismissal in localStorage so it stays
// dismissed across reloads/sessions, and so multiple distinct notices added
// over time don't collide with or re-trigger each other.
export function DismissibleNotice({ id, message }: { id: string; message: string }) {
  // Starts hidden and only reveals itself once the one-time localStorage
  // read below confirms it hasn't already been dismissed -- same
  // avoid-a-flash-of-wrong-state reasoning as ExamProvider's `ready` flag:
  // defaulting to visible would flash the notice on every load for anyone
  // who already dismissed it, before the effect catches up.
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_PREFIX + id);
    if (stored !== "1") {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setVisible(true);
    }
  }, [id]);

  if (!visible) return null;

  const handleDismiss = () => {
    window.localStorage.setItem(STORAGE_PREFIX + id, "1");
    setVisible(false);
  };

  return (
    <div className="w-full border-b border-sky/30 bg-sky/10 px-4 py-2 md:px-6">
      <div className="chat-column mx-auto flex w-full items-start gap-2 text-sm text-sky">
        <span>{message}</span>
        <button
          type="button"
          onClick={handleDismiss}
          aria-label="Dismiss"
          className="shrink-0 text-sky hover:text-ink"
        >
          &times;
        </button>
      </div>
    </div>
  );
}
