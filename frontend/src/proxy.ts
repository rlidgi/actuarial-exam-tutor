import { NextRequest, NextResponse } from "next/server";

// Vanity exam domains -- the entire domain is just the FAM overview page
// (exam-overview-content.tsx), not the whole app. Every path rewrites to
// it (URL bar stays on the vanity domain), so there's no way to browse to
// /chat, /pricing, etc. from here. actuarialexamstutor.com/exams/FAM
// keeps working unchanged -- this only affects requests arriving with one
// of these hostnames.
const VANITY_DOMAINS: Record<string, string> = {
  "examfam.com": "/exams/FAM",
  "www.examfam.com": "/exams/FAM",
};

export function proxy(request: NextRequest) {
  const host = request.headers.get("host")?.toLowerCase() ?? "";
  const target = VANITY_DOMAINS[host];
  if (target && request.nextUrl.pathname !== target) {
    return NextResponse.rewrite(new URL(target, request.url));
  }
  return NextResponse.next();
}

// Every page path, excluding Next internals, the favicon, and anything
// that looks like a static file (has a dot, e.g. /logo-mark.png) -- those
// still need to load unrewritten for the FAM page itself to render.
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};
