import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Vanity referral links -- reuses the existing ?ref= capture in
  // auth-context.tsx entirely unchanged, so a partner's own referral_code
  // (see backend/app/config.py's PARTNER_REFERRAL_CODES) just needs a
  // memorable redirect here, not a dedicated page.
  async redirects() {
    return [
      {
        source: "/pennstate",
        destination: "/?ref=PENNSTATE",
        permanent: false,
      },
      // examfam.com is now the one home for FAM overview content -- see
      // examfam-site/. Permanent so search engines carry this page's
      // existing ranking signal over instead of treating the old URL as
      // just gone.
      {
        source: "/exams/FAM",
        destination: "https://examfam.com",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
