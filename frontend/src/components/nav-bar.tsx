"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export function NavBar() {
  const { token, email, logout, loading } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="border-b border-black/10 dark:border-white/10 px-6 py-3 flex items-center justify-between">
      <Link href="/" className="font-semibold">
        Actuarial Tutor
      </Link>
      {!loading && (
        <nav className="flex items-center gap-4 text-sm">
          {token ? (
            <>
              <Link href="/chat">Chat</Link>
              <Link href="/progress">Progress</Link>
              {email && <span className="text-black/60 dark:text-white/60">{email}</span>}
              <button onClick={handleLogout} className="underline">
                Log out
              </button>
            </>
          ) : (
            <>
              <Link href="/login">Log in</Link>
              <Link href="/register">Register</Link>
            </>
          )}
        </nav>
      )}
    </header>
  );
}
