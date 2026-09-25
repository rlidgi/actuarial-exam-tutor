import type { MetadataRoute } from "next";
import { EXAM_CODES } from "./exams/[code]/exam-overview-data";

const BASE_URL = "https://actuarialexamstutor.com";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: BASE_URL, changeFrequency: "weekly", priority: 1 },
    { url: `${BASE_URL}/pricing`, changeFrequency: "monthly", priority: 0.8 },
    { url: `${BASE_URL}/about`, changeFrequency: "monthly", priority: 0.5 },
    { url: `${BASE_URL}/ambassadors`, changeFrequency: "monthly", priority: 0.5 },
    // FAM excluded -- /exams/FAM now redirects to examfam.com (see
    // next.config.ts), which has its own sitemap; a sitemap entry for a
    // redirecting URL is just noise for crawlers.
    ...EXAM_CODES.filter((code) => code !== "FAM").map((code) => ({
      url: `${BASE_URL}/exams/${code}`,
      changeFrequency: "monthly" as const,
      priority: 0.7,
    })),
  ];
}
