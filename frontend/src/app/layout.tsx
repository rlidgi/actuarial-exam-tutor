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

export const metadata: Metadata = {
  title: {
    default: "Actuarial Exams Tutor -- AI Tutor for SOA Exam P, FM & FAM",
    template: "%s -- Actuarial Exams Tutor",
  },
  description:
    "Your own AI tutor for actuarial exams. Every answer is grounded in the exact SOA-specified " +
    "textbooks, with a citation attached. Free study manual and a 6-message free trial for Exam P, " +
    "FM, and FAM.",
  metadataBase: new URL("https://actuarialexamstutor.com"),
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
