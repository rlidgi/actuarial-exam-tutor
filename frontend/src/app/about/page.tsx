import type { Metadata } from "next";
import AboutContent from "./about-content";

export const metadata: Metadata = {
  title: "About",
  description: "Meet the founder behind Actuarial Exams Tutor and why it was built.",
};

export default function AboutPage() {
  return <AboutContent />;
}
