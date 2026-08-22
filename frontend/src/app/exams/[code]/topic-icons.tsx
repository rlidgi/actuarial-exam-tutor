// Small line-art icon set for the "What Exam X covers" topic cards --
// viewBox/stroke conventions match the exam-picker icons in
// landing-content.tsx (viewBox 0 0 40 40, thin strokes, currentColor so the
// surrounding .topic-card-icon badge controls the color).
import type { JSX } from "react";

function SetsIcon() {
  return (
    <svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true">
      <circle cx="16" cy="20" r="11" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <circle cx="24" cy="20" r="11" fill="none" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  );
}

function CurveIcon() {
  return (
    <svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true">
      <line x1="5" y1="30" x2="35" y2="30" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M6 30 C10 30 12 12 20 12 C28 12 30 30 34 30"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

function ScatterIcon() {
  return (
    <svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true">
      <line x1="7" y1="6" x2="7" y2="33" stroke="currentColor" strokeWidth="1.3" />
      <line x1="7" y1="33" x2="35" y2="33" stroke="currentColor" strokeWidth="1.3" />
      <line
        x1="10"
        y1="28"
        x2="30"
        y2="10"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeDasharray="2 2"
      />
      <circle cx="13" cy="24" r="1.8" fill="currentColor" />
      <circle cx="19" cy="19" r="1.8" fill="currentColor" />
      <circle cx="24" cy="15" r="1.8" fill="currentColor" />
      <circle cx="29" cy="12" r="1.8" fill="currentColor" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true">
      <circle cx="20" cy="21" r="13" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path
        d="M20 13 V21 L26 25"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <line x1="15" y1="5" x2="25" y2="5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function CertificateIcon() {
  return (
    <svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true">
      <rect x="6" y="7" width="24" height="22" rx="2" fill="none" stroke="currentColor" strokeWidth="1.7" />
      <line x1="10" y1="13" x2="26" y2="13" stroke="currentColor" strokeWidth="1.4" />
      <line x1="10" y1="18" x2="22" y2="18" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="27" cy="26" r="7" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M24.5 26 L26.3 27.8 L29.7 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ScaleIcon() {
  return (
    <svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true">
      <line x1="20" y1="7" x2="20" y2="30" stroke="currentColor" strokeWidth="1.7" />
      <line x1="9" y1="12" x2="31" y2="12" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
      <path d="M9 12 L5 21 A4 4 0 0 0 13 21 Z" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
      <path d="M31 12 L27 21 A4 4 0 0 0 35 21 Z" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
      <line x1="14" y1="33" x2="26" y2="33" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

function SurvivalCurveIcon() {
  return (
    <svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true">
      <line x1="6" y1="32" x2="34" y2="32" stroke="currentColor" strokeWidth="1.4" />
      <line x1="6" y1="8" x2="6" y2="32" stroke="currentColor" strokeWidth="1.4" />
      <path
        d="M6 10 C10 10 14 14 18 20 C22 26 26 30 34 31"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true">
      <path
        d="M20 6 L32 10 V19 C32 27 27 32 20 35 C13 32 8 27 8 19 V10 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path
        d="M14 20 L18 24 L27 14"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function BranchIcon() {
  return (
    <svg viewBox="0 0 40 40" width="24" height="24" aria-hidden="true">
      <path
        d="M8 20 L22 10 M8 20 L22 30 M22 10 L34 6 M22 10 L34 16 M22 30 L34 24 M22 30 L34 34"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
      />
      <circle cx="8" cy="20" r="2.2" fill="currentColor" />
      <circle cx="22" cy="10" r="2.2" fill="currentColor" />
      <circle cx="22" cy="30" r="2.2" fill="currentColor" />
      <circle cx="34" cy="6" r="2" fill="currentColor" fillOpacity="0.8" />
      <circle cx="34" cy="16" r="2" fill="currentColor" fillOpacity="0.8" />
      <circle cx="34" cy="24" r="2" fill="currentColor" fillOpacity="0.8" />
      <circle cx="34" cy="34" r="2" fill="currentColor" fillOpacity="0.8" />
    </svg>
  );
}

export const TOPIC_ICONS = {
  sets: SetsIcon,
  curve: CurveIcon,
  scatter: ScatterIcon,
  clock: ClockIcon,
  certificate: CertificateIcon,
  scale: ScaleIcon,
  survivalCurve: SurvivalCurveIcon,
  shield: ShieldIcon,
  branch: BranchIcon,
} satisfies Record<string, () => JSX.Element>;

export type TopicIconKey = keyof typeof TOPIC_ICONS;
