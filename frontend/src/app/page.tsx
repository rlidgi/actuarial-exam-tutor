import type { Metadata } from "next";
import { FAQ_ITEMS } from "@/lib/faq-data";
import LandingContent from "./landing-content";

export const metadata: Metadata = {
  description:
    "Your own AI tutor for actuarial exams. Every answer is grounded in the exact SOA-specified " +
    "textbooks, with a citation attached. Free study manual and a 6-message free trial for Exam P, " +
    "FM, and FAM.",
};

const faqJsonLd = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: FAQ_ITEMS.map((item) => ({
    "@type": "Question",
    name: item.question,
    acceptedAnswer: {
      "@type": "Answer",
      text: item.answer,
    },
  })),
};

export default function LandingPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <LandingContent />
    </>
  );
}
