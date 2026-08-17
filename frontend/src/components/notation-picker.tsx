"use client";

import { useState } from "react";

interface NotationItem {
  label: string;
  title: string;
  snippet: string;
}

// General math applies to every exam; the actuarial group is really an
// FM/FAM concern (life-contingency notation), but it costs nothing to
// offer now and saves rework once those exams are added.
const GENERAL_MATH: NotationItem[] = [
  { label: "\u222B", title: "Integral", snippet: "\\int_{a}^{b} " },
  { label: "\u03A3", title: "Summation", snippet: "\\sum_{i=a}^{b} " },
  { label: "a/b", title: "Fraction", snippet: "\\frac{a}{b}" },
  { label: "\u221A", title: "Square root", snippet: "\\sqrt{a}" },
  { label: "\u221E", title: "Infinity", snippet: "\\infty" },
  { label: "x\u207F", title: "Exponent / power", snippet: "x^{n}" },
];

const ACTUARIAL_NOTATION: NotationItem[] = [
  { label: "\u00E4", title: "Annuity-due", snippet: "\\ddot{a}_{x:\\overline{n}|}" },
  { label: "a\u2099", title: "Annuity-immediate", snippet: "a_{x:\\overline{n}|}" },
  { label: "A", title: "Insurance", snippet: "A_{x:\\overline{n}|}" },
  { label: "\u03B4", title: "Force of interest", snippet: "\\delta" },
  { label: "\u03BC", title: "Force of mortality", snippet: "\\mu_{x}" },
  { label: "\u209CV", title: "Reserve", snippet: "{}_{t}V_{x}" },
];

function NotationGroup({
  label,
  items,
  onInsert,
}: {
  label: string;
  items: NotationItem[];
  onInsert: (snippet: string) => void;
}) {
  return (
    <div className="mb-3 last:mb-0">
      <p className="mb-1 text-xs uppercase tracking-wide text-pencil/75">{label}</p>
      <div className="grid grid-cols-5 gap-1">
        {items.map((item) => (
          <button
            key={item.label}
            type="button"
            title={item.title}
            onClick={() => onInsert(item.snippet)}
            className="rounded border border-rule bg-paper py-1 text-sm text-ink hover:border-ledger-bright hover:bg-ledger/10"
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export function NotationPicker({ onInsert }: { onInsert: (snippet: string) => void }) {
  const [open, setOpen] = useState(false);

  const handleInsert = (snippet: string) => {
    onInsert(`$${snippet}$`);
    setOpen(false);
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        title="Insert math or actuarial notation"
        className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-md border border-rule bg-paper-raised text-pencil hover:border-ledger-bright hover:text-ledger-bright"
      >
        &Sigma;
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute bottom-full left-0 z-20 mb-2 w-60 max-w-[calc(100vw-2rem)] rounded-lg border border-rule bg-paper-raised p-3 shadow-lg">
            <NotationGroup label="General math" items={GENERAL_MATH} onInsert={handleInsert} />
            <NotationGroup
              label="Actuarial notation"
              items={ACTUARIAL_NOTATION}
              onInsert={handleInsert}
            />
          </div>
        </>
      )}
    </div>
  );
}
