import type { ReactNode } from "react";
import Link from "next/link";

export default function PublicGroupLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col">
      <header className="flex items-center justify-between border-b border-black/10 px-6 py-3 dark:border-white/10">
        <Link href="/" className="font-semibold">
          Actuarial Tutor
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/login">Log in</Link>
          <Link href="/register">Register</Link>
        </nav>
      </header>
      <main className="flex flex-1 flex-col">{children}</main>
    </div>
  );
}
