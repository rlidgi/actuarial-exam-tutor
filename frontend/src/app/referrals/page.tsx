import type { Metadata } from "next";
import ReferralsContent from "./referrals-content";

export const metadata: Metadata = {
  title: "Referral Program",
  description:
    "Refer a friend to Actuarial Exams Tutor -- they get 25% off their first month, and you get $10 credit toward your own subscription.",
};

export default function ReferralProgramPage() {
  return <ReferralsContent />;
}
