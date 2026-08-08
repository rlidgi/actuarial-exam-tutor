import type { ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";

export function MarketingHeader({ children }: { children: ReactNode }) {
  return (
    <header className="landing-nav">
      <Link href="/" className="wordmark-group">
        <Image src="/logo-mark.png" alt="" width={34} height={34} className="wordmark-mark" />
        <span className="wordmark-divider" />
        <Image
          src="/logo-text.png"
          alt="Actuarial Exams Tutor"
          width={220}
          height={26}
          className="wordmark-text"
        />
      </Link>
      <div className="landing-nav-links">{children}</div>
    </header>
  );
}
