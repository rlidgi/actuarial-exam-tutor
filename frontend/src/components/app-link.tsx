"use client";

import Link from "next/link";
import type { AnchorHTMLAttributes, ReactNode } from "react";

// Empty by default (relative paths, same-origin client-side nav) --
// examfam-site's build overrides this to the main app's origin, since it
// has no routes of its own besides "/": every link that would otherwise
// point to a route that doesn't exist there (About, Pricing, the study
// manual, ...) needs to land on the real app instead. See
// examfam-site/next.config.ts.
export const EXTERNAL_ORIGIN = process.env.NEXT_PUBLIC_EXTERNAL_ORIGIN ?? "";

export function externalHref(path: string): string {
  return `${EXTERNAL_ORIGIN}${path}`;
}

// For imperative navigation (router.push callers) -- same reasoning as
// AppLink, but a Next.js router transition can't cross origins at all, so
// this falls back to a full browser navigation instead.
export function navigateToApp(router: { push: (path: string) => void }, path: string) {
  if (EXTERNAL_ORIGIN) {
    // Not a component/hook, so react-hooks/immutability doesn't apply here
    // the way it does to the JSX-returning callers of this function.
    window.location.href = externalHref(path);
  } else {
    router.push(path);
  }
}

// Drop-in for next/link: a same-app relative path everywhere except
// examfam-site, where it becomes a plain cross-origin <a> to the main app
// (a client-side Link transition can't cross origins anyway).
export function AppLink({
  href,
  children,
  ...rest
}: { href: string; children: ReactNode } & AnchorHTMLAttributes<HTMLAnchorElement>) {
  if (EXTERNAL_ORIGIN) {
    return (
      <a href={externalHref(href)} {...rest}>
        {children}
      </a>
    );
  }
  return (
    <Link href={href} {...rest}>
      {children}
    </Link>
  );
}
