import type { Metadata } from "next";
import ContactContent from "./contact-content";

export const metadata: Metadata = {
  title: "Contact Us",
  description: "Get in touch with the Actuarial Exams Tutor team.",
};

export default function ContactPage() {
  return <ContactContent />;
}
