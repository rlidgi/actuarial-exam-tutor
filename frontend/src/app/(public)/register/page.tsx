"use client";

import { useRouter } from "next/navigation";
import { SignInModal } from "@/components/sign-in-modal";
import { useDocumentTitle } from "@/lib/use-document-title";

// Compatibility route for bookmarks/inbound links to the old /register page
// -- registration and sign-in are the same modal now (Supabase creates the
// account on first sign-in), see app/page.tsx.
export default function RegisterPage() {
  const router = useRouter();
  useDocumentTitle("Sign In");
  return <SignInModal onClose={() => router.push("/")} />;
}
