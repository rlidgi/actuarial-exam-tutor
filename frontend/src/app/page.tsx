import type { Metadata } from "next";
import LandingContent from "./landing-content";

export const metadata: Metadata = {
  description:
    "Your own AI tutor for actuarial exams. Every answer is grounded in the exact SOA-specified " +
    "textbooks, with a citation attached. Free study manual and a 6-message free trial for Exam P, " +
    "FM, and FAM.",
};

export default function LandingPage() {
  return <LandingContent />;
}
