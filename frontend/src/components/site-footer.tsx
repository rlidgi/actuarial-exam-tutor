export function SiteFooter() {
  return (
    <footer className="site-footer">
      <span>&copy; Actuarial Exams Tutor. All Rights Reserved 2026.</span>
      {/* Static self-contained HTML files (frontend/public/), not React
          routes -- a plain reload is correct here, not client-side nav. */}
      <a href="/terms.html">Terms of Service</a>
      <a href="/privacy.html">Privacy Policy</a>
      <a
        href="https://www.facebook.com/profile.php?id=61592801835167"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Facebook"
        className="site-footer-icon"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M22 12a10 10 0 1 0-11.56 9.88v-6.99H7.9V12h2.54V9.8c0-2.5 1.49-3.89 3.77-3.89 1.09 0 2.24.2 2.24.2v2.46h-1.26c-1.24 0-1.63.77-1.63 1.56V12h2.77l-.44 2.89h-2.33v6.99A10 10 0 0 0 22 12Z" />
        </svg>
      </a>
    </footer>
  );
}
