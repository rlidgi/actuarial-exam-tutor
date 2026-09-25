import type { Metadata } from "next";
import AmbassadorsContent from "./ambassadors-content";

export const metadata: Metadata = {
  title: "Campus Ambassador Program",
  description:
    "Become an Actuarial Exams Tutor Campus Ambassador -- earn $5 for every student at your school who subscribes, get lifetime access for your next preliminary exam, and help your campus's actuarial community succeed.",
};

export default function AmbassadorsPage() {
  return <AmbassadorsContent />;
}
