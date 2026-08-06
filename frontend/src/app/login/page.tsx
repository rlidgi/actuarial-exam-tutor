"use client";

import { AuthForm } from "@/components/auth-form";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const { login } = useAuth();

  return <AuthForm title="Log in" submitLabel="Log in" onSubmit={login} />;
}
