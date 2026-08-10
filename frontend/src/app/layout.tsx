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

const SITE_TITLE = "Actuarial Exams Tutor -- AI Tutor for SOA Exam P, FM & FAM";
const SITE_DESCRIPTION =
  "Your own AI tutor for actuarial exams. Every answer is grounded in the exact SOA-specified " +
  "textbooks, with a citation attached. Free study manual and a 6-message free trial for Exam P, " +
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
        url: "/screenshotimage.png",
        width: 1536,
        height: 1024,
        alt: "Actuarial Exams Tutor chat -- a worked problem with a textbook citation",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    images: ["/screenshotimage.png"],
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
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
