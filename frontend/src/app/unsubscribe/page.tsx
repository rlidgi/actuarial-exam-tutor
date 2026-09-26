import type { Metadata } from "next";
import { Suspense } from "react";
import UnsubscribeContent from "./unsubscribe-content";

export const metadata: Metadata = {
  title: "Unsubscribe",
  robots: { index: false },
};

export default function UnsubscribePage() {
  // useSearchParams (for the token) needs a Suspense boundary for static
  // rendering -- same as landing-content.tsx's SignInErrorBanner.
  return (
    <Suspense fallback={null}>
      <UnsubscribeContent />
    </Suspense>
  );
}
