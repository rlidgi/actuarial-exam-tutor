import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { MarketingHeader } from "@/components/marketing-header";
import { SiteFooter } from "@/components/site-footer";

export const metadata: Metadata = {
  title: "About",
  description: "Meet the founder behind Actuarial Exams Tutor and why it was built.",
};

export default function AboutPage() {
  return (
    <div className="landing">
      <MarketingHeader>
        <Link className="btn" href="/">
          Home
        </Link>
      </MarketingHeader>

      <article className="legal-body">
        <h1>About Actuarial Exams Tutor</h1>

        <h2>Our Mission</h2>
        <p>
          Preparing for actuarial exams is one of the most demanding academic challenges a student
          can undertake. Success requires more than memorization, it requires a deep understanding
          of probability, statistics, financial mathematics, risk modeling, and the ability to
          apply those concepts to unfamiliar problems under exam conditions.
        </p>
        <div style={{ height: '8px' }} /> {/* Adjust '8px' to make it smaller or larger */}
        <p>
          Actuarial Exam Tutor was created with a simple mission: to make high-quality actuarial
          education more personalized, accessible, and effective through the responsible use of
          artificial intelligence.
        </p>
        <div style={{ height: '8px' }} /> {/* Adjust '8px' to make it smaller or larger */}
        <p>
          Rather than replacing traditional study materials, the platform is designed to complement
          them by providing instant explanations, step-by-step guidance, personalized feedback, and
          interactive learning tailored to each student&rsquo;s level of understanding.
        </p>

        <h2>Meet the Founder</h2>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <Image
            src="/founder.png"
            alt="Yaron Lidgi"
            width={64}
            height={64}
            style={{ borderRadius: "50%", objectFit: "cover" }}
          />
          <p style={{ margin: 0 }}>
            <strong>Yaron Lidgi</strong>
            <br />
            Founder, Actuarial Exams Tutor
          </p>
        </div>
        <div style={{ height: '8px' }} /> {/* Adjust '8px' to make it smaller or larger */}
        <p>
          After years of taking exams, I expect to attain an ASA designation at the Society of
          Actuaries in Fall 2026. Beyond my actuarial expertise, I also have extensive training and
          experience in the natural language space, specifically with large language models.
          I currently work as an independent consultant on projects related to both actuarial
          science and artificial intelligence.
        </p>
        <div style={{ height: '8px' }} /> {/* Adjust '8px' to make it smaller or larger */}
        <p>
          Preparing for actuarial exams is largely a self-directed journey. While high-quality
          study manuals do an excellent job of presenting the material, they cannot answer your
          questions, adapt their explanations, or guide you through difficult concepts. A personal
          tutor can provide that level of support, but for many students, it simply isn&rsquo;t
          affordable. I built Actuarial Exam Tutor to bridge that gap. By combining advances in artificial
          intelligence with trusted actuarial study resources, my goal was to provide every student
          with the experience of having a knowledgeable tutor available whenever they need one.
        </p>
      </article>

      <SiteFooter />
    </div>
  );
}
