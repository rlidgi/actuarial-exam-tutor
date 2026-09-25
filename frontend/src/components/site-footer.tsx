import { AppLink, externalHref } from "./app-link";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer-social">
        <a
          href="https://www.facebook.com/profile.php?id=61594026569737"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="Facebook"
          className="site-footer-icon"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
            <path
              fill="currentColor"
              d="M22 12a10 10 0 1 0-11.56 9.88v-6.99H7.9V12h2.54V9.8c0-2.5 1.49-3.89 3.78-3.89 1.09 0 2.24.2 2.24.2v2.46h-1.26c-1.24 0-1.63.77-1.63 1.56V12h2.78l-.44 2.89h-2.34v6.99A10 10 0 0 0 22 12Z"
            />
          </svg>
        </a>
      </div>
      <nav className="site-footer-links" aria-label="Footer">
        {/* A real Next.js route -- client-side nav. */}
        <AppLink href="/contact">Contact Us</AppLink>
        {/* Static self-contained HTML files (frontend/public/), not React
            routes -- a plain reload is correct here, not client-side nav. */}
        <a href={externalHref("/terms.html")}>Terms</a>
        <a href={externalHref("/privacy.html")}>Privacy</a>
      </nav>
      <span className="site-footer-copyright">Actuarial Exams Tutor 2026</span>
    </footer>
  );
}
