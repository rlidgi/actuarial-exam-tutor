import { NextRequest, NextResponse } from "next/server";

// Vanity exam domains -- visiting the bare domain shows that exam's
// overview page (exam-overview-content.tsx) without the URL bar changing,
// so e.g. examfam.com "is" the FAM overview page rather than redirecting
// to actuarialexamstutor.com/exams/FAM (which keeps working unchanged).
// Everything else on these domains (login, /chat, API calls, ...) still
// works unchanged since it's the same app/session, just reached via a
// different hostname.
const VANITY_DOMAINS: Record<string, string> = {
  "examfam.com": "/exams/FAM",
  "www.examfam.com": "/exams/FAM",
};

export function proxy(request: NextRequest) {
  const host = request.headers.get("host")?.toLowerCase() ?? "";
  const target = VANITY_DOMAINS[host];
  if (target) {
    return NextResponse.rewrite(new URL(target, request.url));
  }
  return NextResponse.next();
}

// Root path only -- proxy doesn't need to run on every request site-wide,
// just to decide what "/" resolves to on a vanity domain.
export const config = {
  matcher: "/",
};
