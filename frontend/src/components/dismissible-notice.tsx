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
    <div className="chat-column mx-auto mt-3 w-full px-4 md:px-6">
      <div className="relative rounded-lg border border-sky/30 bg-sky/10 py-2.5 pl-4 pr-10 text-sm text-sky">
        <span aria-hidden="true" className="mr-1.5">
          &#9432;
        </span>
        <span>{message}</span>
        <button
          type="button"
          onClick={handleDismiss}
          aria-label="Dismiss"
          className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-lg leading-none text-sky hover:text-ink"
        >
          &times;
        </button>
      </div>
    </div>
  );
}
