// Per-category dashboard icons, ported from the discarded app's
// _topic_icon.html. That app's topic keys and this app's syllabus category
// names describe the same 18 syllabus sections across the 3 exams (same
// underlying syllabus, different wording) -- mapped here by the exact
// category name student_service.py's profile_progress_summary returns.
// Falls back to a generic icon for anything unmatched (e.g. a future
// syllabus section) rather than breaking.

const ICONS: Record<string, () => React.JSX.Element> = {
  "General Probability": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <circle cx="16" cy="20" r="12" fill="var(--ledger-bright)" fillOpacity="0.18" stroke="var(--ledger)" strokeWidth="1.6" />
      <circle cx="24" cy="20" r="12" fill="var(--gold)" fillOpacity="0.18" stroke="var(--ledger)" strokeWidth="1.6" />
    </svg>
  ),
  "Univariate Random Variables": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <path d="M4 28 Q 12 28 16 12 Q 20 28 28 28" fill="none" stroke="var(--ledger)" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="4" y1="28" x2="34" y2="28" stroke="var(--rule)" strokeWidth="1.6" />
    </svg>
  ),
  "Multivariate Random Variables": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <line x1="6" y1="30" x2="6" y2="8" stroke="var(--rule)" strokeWidth="1.6" />
      <line x1="6" y1="30" x2="32" y2="30" stroke="var(--rule)" strokeWidth="1.6" />
      <circle cx="14" cy="22" r="2.4" fill="var(--ledger)" />
      <circle cx="20" cy="14" r="2.4" fill="var(--gold)" />
      <circle cx="26" cy="24" r="2.4" fill="var(--sky)" />
      <circle cx="22" cy="20" r="2.4" fill="var(--ledger-bright)" />
    </svg>
  ),
  "Time Value of Money": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <circle cx="20" cy="20" r="13" fill="none" stroke="var(--ledger)" strokeWidth="1.8" />
      <line x1="20" y1="20" x2="20" y2="11" stroke="var(--ledger)" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="20" y1="20" x2="26" y2="23" stroke="var(--gold)" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
  Annuities: () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <line x1="5" y1="30" x2="35" y2="30" stroke="var(--rule)" strokeWidth="1.6" />
      <line x1="9" y1="30" x2="9" y2="14" stroke="var(--ledger)" strokeWidth="2.2" strokeLinecap="round" />
      <line x1="18" y1="30" x2="18" y2="20" stroke="var(--ledger-bright)" strokeWidth="2.2" strokeLinecap="round" />
      <line x1="27" y1="30" x2="27" y2="10" stroke="var(--gold)" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  ),
  Loans: () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <rect x="6" y="10" width="7" height="22" rx="1" fill="var(--ledger)" />
      <rect x="17" y="16" width="7" height="16" rx="1" fill="var(--ledger-bright)" />
      <rect x="28" y="22" width="7" height="10" rx="1" fill="var(--gold)" />
    </svg>
  ),
  Bonds: () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <rect x="9" y="6" width="22" height="16" rx="1.5" fill="none" stroke="var(--ledger)" strokeWidth="1.6" />
      <line x1="13" y1="11" x2="27" y2="11" stroke="var(--rule)" strokeWidth="1.4" />
      <line x1="13" y1="15" x2="23" y2="15" stroke="var(--rule)" strokeWidth="1.4" />
      <circle cx="20" cy="27" r="6" fill="var(--gold)" fillOpacity="0.25" stroke="var(--gold)" strokeWidth="1.6" />
    </svg>
  ),
  "General Cash Flows, Portfolios, and Asset Liability Management": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <line x1="20" y1="8" x2="20" y2="30" stroke="var(--ledger)" strokeWidth="1.8" />
      <line x1="8" y1="14" x2="32" y2="14" stroke="var(--ledger)" strokeWidth="1.8" />
      <path d="M8 14 L4 22 A5 4 0 0 0 12 22 Z" fill="var(--sky)" fillOpacity="0.3" stroke="var(--sky)" strokeWidth="1.4" />
      <path d="M32 14 L28 22 A5 4 0 0 0 36 22 Z" fill="var(--gold)" fillOpacity="0.3" stroke="var(--gold)" strokeWidth="1.4" />
    </svg>
  ),
  "Short-Term Insurance and Reinsurance Coverages": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <path d="M8 18 A12 12 0 0 1 32 18 Z" fill="var(--sky)" fillOpacity="0.25" stroke="var(--sky)" strokeWidth="1.6" />
      <line x1="20" y1="18" x2="20" y2="32" stroke="var(--ledger)" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M20 32 q0 4 4 3" fill="none" stroke="var(--ledger)" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  ),
  "Severity, Frequency, and Aggregate Models": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <rect x="6" y="22" width="5" height="10" fill="var(--rule)" />
      <rect x="13" y="14" width="5" height="18" fill="var(--rule)" />
      <rect x="20" y="18" width="5" height="14" fill="var(--rule)" />
      <rect x="27" y="25" width="5" height="7" fill="var(--rule)" />
      <path d="M5 20 Q 16 4 34 24" fill="none" stroke="var(--gold)" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
  "Parametric Estimation": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <circle cx="20" cy="20" r="12" fill="none" stroke="var(--ledger)" strokeWidth="1.6" />
      <circle cx="20" cy="20" r="7" fill="none" stroke="var(--ledger-bright)" strokeWidth="1.6" />
      <circle cx="20" cy="20" r="2.2" fill="var(--gold)" />
    </svg>
  ),
  "Introduction to Credibility": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <path
        d="M20 6 L32 10 V19 C32 27 27 32 20 34 C13 32 8 27 8 19 V10 Z"
        fill="var(--ledger-bright)"
        fillOpacity="0.15"
        stroke="var(--ledger)"
        strokeWidth="1.6"
      />
      <path d="M14 20 L18 24 L27 14" fill="none" stroke="var(--gold)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  "Pricing and Reserving for Short-Term Insurance Coverages": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <path d="M7 20 L18 9 H31 V22 L20 33 Z" fill="none" stroke="var(--ledger)" strokeWidth="1.6" strokeLinejoin="round" />
      <circle cx="24" cy="15" r="2.2" fill="var(--gold)" />
    </svg>
  ),
  "Option Pricing Fundamentals": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <circle cx="7" cy="20" r="2.2" fill="var(--ledger)" />
      <circle cx="20" cy="10" r="2.2" fill="var(--ledger-bright)" />
      <circle cx="20" cy="30" r="2.2" fill="var(--ledger-bright)" />
      <circle cx="33" cy="6" r="2" fill="var(--gold)" />
      <circle cx="33" cy="16" r="2" fill="var(--gold)" />
      <circle cx="33" cy="24" r="2" fill="var(--gold)" />
      <circle cx="33" cy="34" r="2" fill="var(--gold)" />
      <line x1="7" y1="20" x2="20" y2="10" stroke="var(--rule)" strokeWidth="1.4" />
      <line x1="7" y1="20" x2="20" y2="30" stroke="var(--rule)" strokeWidth="1.4" />
      <line x1="20" y1="10" x2="33" y2="6" stroke="var(--rule)" strokeWidth="1.4" />
      <line x1="20" y1="10" x2="33" y2="16" stroke="var(--rule)" strokeWidth="1.4" />
      <line x1="20" y1="30" x2="33" y2="24" stroke="var(--rule)" strokeWidth="1.4" />
      <line x1="20" y1="30" x2="33" y2="34" stroke="var(--rule)" strokeWidth="1.4" />
    </svg>
  ),
  "Long-Term Insurance Coverages and Retirement Financial Security Programs": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <line x1="20" y1="34" x2="20" y2="18" stroke="var(--ledger)" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M20 22 Q12 20 10 10 Q20 12 20 22" fill="var(--ledger-bright)" fillOpacity="0.3" stroke="var(--ledger-bright)" strokeWidth="1.4" />
      <path d="M20 18 Q28 16 30 6 Q20 8 20 18" fill="var(--gold)" fillOpacity="0.3" stroke="var(--gold)" strokeWidth="1.4" />
    </svg>
  ),
  "Mortality Models": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <line x1="5" y1="30" x2="5" y2="8" stroke="var(--rule)" strokeWidth="1.4" />
      <line x1="5" y1="30" x2="34" y2="30" stroke="var(--rule)" strokeWidth="1.4" />
      <path d="M6 10 Q 14 11 18 18 Q 26 26 33 28" fill="none" stroke="var(--ledger)" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
  "Present Value Random Variables for Long-Term Insurance Coverages": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <circle cx="30" cy="12" r="5" fill="var(--gold)" fillOpacity="0.25" stroke="var(--gold)" strokeWidth="1.6" />
      <circle cx="10" cy="28" r="5" fill="var(--ledger-bright)" fillOpacity="0.25" stroke="var(--ledger)" strokeWidth="1.6" />
      <path d="M25 15 Q17 21 15 24" fill="none" stroke="var(--ledger)" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M15 24 L19 23 L17 27 Z" fill="var(--ledger)" />
    </svg>
  ),
  "Premium and Policy Value Calculation for Long-Term Insurance Coverages": () => (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <rect x="6" y="12" width="28" height="18" rx="2" fill="none" stroke="var(--ledger)" strokeWidth="1.6" />
      <rect x="22" y="18" width="10" height="7" rx="1" fill="var(--gold)" fillOpacity="0.3" stroke="var(--gold)" strokeWidth="1.4" />
      <circle cx="27" cy="21.5" r="1.6" fill="var(--gold)" />
    </svg>
  ),
};

function GenericTopicIcon() {
  return (
    <svg viewBox="0 0 40 40" width="26" height="26" aria-hidden="true">
      <rect x="7" y="20" width="6" height="12" rx="1" fill="var(--ledger-bright)" />
      <rect x="17" y="12" width="6" height="20" rx="1" fill="var(--ledger)" />
      <rect x="27" y="16" width="6" height="16" rx="1" fill="var(--gold)" />
    </svg>
  );
}

export function TopicIcon({ categoryName }: { categoryName: string }) {
  const Icon = ICONS[categoryName];
  return Icon ? <Icon /> : <GenericTopicIcon />;
}
