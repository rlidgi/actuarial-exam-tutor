export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer-legal">
        <span>&copy; Actuarial Exams Tutor. All Rights Reserved 2026.</span>
        {/* Static self-contained HTML files (frontend/public/), not React
            routes -- a plain reload is correct here, not client-side nav. */}
        <a href="/terms.html">Terms of Service</a>
        <a href="/privacy.html">Privacy Policy</a>
      </div>
      <a
        href="https://www.facebook.com/profile.php?id=61592801835167"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Facebook"
        className="site-footer-icon"
      >
        <svg width="34" height="34" viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="12" fill="var(--pencil)" />
          <path
            fill="var(--paper)"
            d="M15.5 12.3h-2.1v7.6h-3.1v-7.6H8.8v-2.7h1.5V8c0-1.6.8-3.4 3.5-3.4h2.1v2.6h-1.5c-.3 0-.7.2-.7.9v1.5h2.2l-.4 2.7Z"
          />
        </svg>
      </a>
    </footer>
  );
}
