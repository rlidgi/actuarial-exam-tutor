"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { AuthForm } from "@/components/auth-form";
import { useAuth } from "@/lib/auth-context";

function ExpiredBanner() {
  const searchParams = useSearchParams();
  if (searchParams.get("expired") !== "1") return null;

  return (
    <p className="text-sm text-black/60 dark:text-white/60">
      Your session expired -- log in again to continue.
    </p>
  );
}

export default function LoginPage() {
  const { login } = useAuth();

  return (
    <AuthForm
      title="Log in"
      submitLabel="Log in"
      onSubmit={login}
      banner={
        <Suspense fallback={null}>
          <ExpiredBanner />
        </Suspense>
      }
    />
  );
}
