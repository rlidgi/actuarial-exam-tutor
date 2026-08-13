// Thin wrapper around the global gtag() function loaded via the Google Ads
// script in layout.tsx -- reports a conversion for one of the conversion
// actions configured in Google Ads. Passing `email` uses Enhanced
// Conversions (gtag.js hashes it client-side before sending) for better
// match rates than the base conversion event alone.
declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
  }
}

const ADS_ACCOUNT_ID = "AW-18381595346";

// Conversion action labels -- see Google Ads > Tools & Settings >
// Conversions > (action) > Tag setup for the source of truth.
export const SIGNUP_CONVERSION_LABEL = "VYP4CJnI1OAcENLFg71E";
export const SUBSCRIBE_CONVERSION_LABEL = "4dysCJzI1OAcENLFg71E";

export function reportAdsConversion(conversionLabel: string, email?: string) {
  if (typeof window === "undefined" || !window.gtag) return;
  if (email) {
    window.gtag("set", "user_data", { email });
  }
  window.gtag("event", "conversion", {
    send_to: `${ADS_ACCOUNT_ID}/${conversionLabel}`,
    value: 1.0,
    currency: "USD",
  });
}
