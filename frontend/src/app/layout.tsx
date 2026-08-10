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

const SITE_TITLE = "Actuarial Exams Tutor -- AI Tutor for SOA Exam P, FM & FAM";
const SITE_DESCRIPTION =
  "Your own AI tutor for actuarial exams. Every answer is grounded in the exact SOA/CASACT-specified " +
  "textbooks. Free study manual and a 6-message free trial for Exam P, " +
  "FM, and FAM.";

export const metadata: Metadata = {
  title: {
    default: SITE_TITLE,
    template: "%s -- Actuarial Exams Tutor",
  },
  description: SITE_DESCRIPTION,
  metadataBase: new URL("https://actuarialexamstutor.com"),
  openGraph: {
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    url: "https://actuarialexamstutor.com",
    siteName: "Actuarial Exams Tutor",
    type: "website",
    images: [
      {
        url: "/screenshotimage3.png",
        width: 1254,
        height: 1254,
        alt: "Actuarial Exams Tutor",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    images: ["/screenshotimage3.png"],
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {/* Google Ads conversion tracking (gtag.js) -- afterInteractive loads
            it once the page is interactive, rather than blocking initial
            render, and next/script here in the root layout applies it to
            every route instead of needing to repeat it per page. */}
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=AW-18381595346"
          strategy="afterInteractive"
        />
        <Script id="google-ads-gtag" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'AW-18381595346');
          `}
        </Script>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
