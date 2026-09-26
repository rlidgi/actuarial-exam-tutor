// P/FM/FAM icons, drawn in each exam's own accent color -- shared by the
// landing page's "Prepare for Your Next Exam" cards and the pricing cards.
export const EXAM_ICONS: Record<string, (color: string) => React.JSX.Element> = {
  P: (color) => (
    <svg viewBox="0 0 40 40" width="44" height="44" aria-hidden="true">
      <line
        x1="6"
        y1="32"
        x2="34"
        y2="32"
        stroke="var(--rule)"
        strokeWidth="1.6"
      />
      <rect
        x="10"
        y="22"
        width="6"
        height="10"
        rx="1"
        fill={color}
        fillOpacity="0.75"
      />
      <rect
        x="19"
        y="15"
        width="6"
        height="17"
        rx="1"
        fill={color}
        fillOpacity="0.9"
      />
      <rect x="28" y="9" width="6" height="23" rx="1" fill={color} />
    </svg>
  ),
  FM: (color) => (
    <svg viewBox="0 0 40 40" width="44" height="44" aria-hidden="true">
      <path
        d="M6 28 L15 19 L21 24 L34 10"
        fill="none"
        stroke={color}
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M26 10 H34 V18"
        fill="none"
        stroke={color}
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ),
  FAM: (color) => (
    <svg viewBox="0 0 40 40" width="44" height="44" aria-hidden="true">
      <path
        d="M20 12 C17 9 11 8 6 9 V27 C11 26 17 27 20 30 C23 27 29 26 34 27 V9 C29 8 23 9 20 12 Z"
        fill="none"
        stroke={color}
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <line x1="20" y1="12" x2="20" y2="30" stroke={color} strokeWidth="1.8" />
    </svg>
  ),
};
