import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Authenticated app pages -- nothing for a crawler to index behind
      // the login redirect, and the OAuth callback carries a one-time token.
      disallow: ["/chat", "/manual", "/progress", "/subscribe", "/auth/"],
    },
    sitemap: "https://actuarialexamstutor.com/sitemap.xml",
  };
}
