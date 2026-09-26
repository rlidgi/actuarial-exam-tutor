import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const TITLE = "Exam FAM | Actuarial Exams Tutor";
const DESCRIPTION =
  "Free study manual and formula sheet, plus AI tutor access, for Exam FAM. See what's free and what's included with a subscription.";

// Tells Google what name to show for this site in organic search results
// (the line next to the favicon, and a signal toward using a branded
// title too) -- without this, Google falls back to displaying the raw
// domain instead. Same pattern as the main app's layout.tsx.
const websiteJsonLd = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "Actuarial Exams Tutor",
  url: "https://examfam.com",
};

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  metadataBase: new URL("https://examfam.com"),
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: "https://examfam.com",
    siteName: "Actuarial Exams Tutor",
    type: "website",
    // Reused from the main app rather than duplicated here -- always the
    // current image, no separate asset to keep in sync.
    images: [
      {
        url: "https://actuarialexamstutor.com/og-preview.png",
        width: 1200,
        height: 630,
        alt: "Actuarial Exams Tutor -- a real tutoring exchange with worked math",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
    images: ["https://actuarialexamstutor.com/og-preview.png"],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {/* Microsoft Clarity session recording -- this site's own Clarity
            project (the main app's layout.tsx loads a different one), same
            afterInteractive next/script pattern as the main app. */}
        <Script id="ms-clarity" strategy="afterInteractive">
          {`
            (function(c,l,a,r,i,t,y){
                c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
                t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
                y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
            })(window, document, "clarity", "script", "yo7sfs6x0k");
          `}
        </Script>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteJsonLd) }}
        />
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
