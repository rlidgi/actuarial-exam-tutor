import type { MetadataRoute } from "next";

export const dynamic = "force-static";

// One page, one URL -- see next.config.ts, this whole site is a single
// static export.
export default function sitemap(): MetadataRoute.Sitemap {
  return [{ url: "https://examfam.com", changeFrequency: "monthly", priority: 1 }];
}
