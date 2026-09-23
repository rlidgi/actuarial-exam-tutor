import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
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

const TITLE = "Exam FAM";
const DESCRIPTION =
  "Free study manual and formula sheet, plus AI tutor access, for Exam FAM. See what's free and what's included with a subscription.";

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
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
