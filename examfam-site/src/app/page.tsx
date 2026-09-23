import ExamOverviewContent from "@/app/exams/[code]/exam-overview-content";

// examfam.com is this one page, nothing else -- the exact same component
// actuarialexamstutor.com/exams/FAM renders, just hardcoded to "FAM" since
// there's no [code] route here (see next.config.ts / proxy.ts's absence:
// this whole site is a single static export).
export default function Page() {
  return <ExamOverviewContent code="FAM" />;
}
