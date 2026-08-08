export function SiteFooter() {
  return (
    <footer className="site-footer">
      <span>&copy; Actuarial Exams Tutor. All Rights Reserved 2026.</span>
      {/* Static self-contained HTML files (frontend/public/), not React
          routes -- a plain reload is correct here, not client-side nav. */}
      <a href="/terms.html">Terms of Service</a>
      <a href="/privacy.html">Privacy Policy</a>
    </footer>
  );
}
