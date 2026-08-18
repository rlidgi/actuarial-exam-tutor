"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { SignInModal } from "@/components/sign-in-modal";
import { useDocumentTitle } from "@/lib/use-document-title";

function ExpiredBanner() {
  const searchParams = useSearchParams();
  if (searchParams.get("expired") !== "1") return null;

  return (
    <p className="mb-4 text-sm text-pencil-soft">
      Your session expired -- sign in again to continue.
    </p>
  );
}

// Compatibility route for bookmarks/inbound links to the old /login page --
// sign-in now lives in a modal (see app/page.tsx), so this just opens it
// over the landing page destination rather than rendering its own form.
export default function LoginPage() {
  const router = useRouter();
  useDocumentTitle("Sign In");
  return (
    <SignInModal
      onClose={() => router.push("/")}
      banner={
        <Suspense fallback={null}>
          <ExpiredBanner />
        </Suspense>
      }
    />
  );
}
