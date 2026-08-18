import type { Metadata } from "next";
import { Suspense } from "react";
import PricingContent from "./pricing-content";

export const metadata: Metadata = {
  title: "Pricing",
  description:
    "$25/month per exam, unlimited use. Subscribe only to the exams you're studying for -- " +
    "cancel anytime, no commitment.",
};

export default function PricingPage() {
  // Public, unlike the app's own pages -- matches the old app: browsable
  // signed out, gates only the Subscribe action itself via a sign-in link.
  return (
    <Suspense fallback={null}>
      <PricingContent />
    </Suspense>
  );
}
