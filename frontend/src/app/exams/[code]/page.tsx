import type { Metadata } from "next";
import { notFound } from "next/navigation";
import ExamOverviewContent from "./exam-overview-content";
import { EXAM_CODES, EXAM_OVERVIEW, type ExamCode } from "./exam-overview-data";

// FAM excluded -- its overview now lives at examfam.com (which imports
// ExamOverviewContent directly, unaffected by this file) instead of here.
// next.config.ts redirects /exams/FAM there, but this app no longer
// builds or serves that content at all, as a second guard against ever
// serving it from a stale cache independently of the redirect.
const ROUTE_EXAM_CODES = EXAM_CODES.filter((code) => code !== "FAM");

export function generateStaticParams() {
  return ROUTE_EXAM_CODES.map((code) => ({ code }));
}

function resolveExam(code: string): ExamCode | null {
  const upper = code.toUpperCase();
  return (ROUTE_EXAM_CODES as readonly string[]).includes(upper) ? (upper as ExamCode) : null;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ code: string }>;
}): Promise<Metadata> {
  const { code } = await params;
  const examCode = resolveExam(code);
  if (!examCode) return {};
  const exam = EXAM_OVERVIEW[examCode];
  return {
    title: `${exam.fullName} Resources`,
    description: `Free study manual and formula sheet, plus AI tutor access, for ${exam.fullName}. See what's free and what's included with a subscription.`,
  };
}

export default async function ExamOverviewPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = await params;
  const examCode = resolveExam(code);
  if (!examCode) notFound();
  return <ExamOverviewContent code={examCode} />;
}
