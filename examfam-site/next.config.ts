import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Static export -- this site is one page with no server (no auth
  // callbacks, no API routes of its own; everything talks to the same
  // backend the main app uses). Deployed to its own Azure Static Web App
  // resource so its CDN cache is fully isolated from actuarialexamstutor.com
  // (see the commit that added this directory for why that isolation
  // matters).
  output: "export",
  images: {
    unoptimized: true,
  },
  // Source files are imported directly from ../frontend/src (see
  // tsconfig.json's @/* path) to keep this page byte-identical to
  // actuarialexamstutor.com/exams/FAM rather than a copy that can drift --
  // this points Next at the actual monorepo root so it traces file
  // dependencies correctly instead of guessing from the two sibling
  // lockfiles.
  outputFileTracingRoot: path.join(__dirname, ".."),
};

export default nextConfig;
