import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // A production build and a running dev server both write to `.next` and
  // overwrite each other's manifests, which leaves the dev server throwing
  // ENOENT for files it expects to exist. `npm run build:check` sets this so a
  // verification build lands somewhere else and cannot disturb dev.
  distDir: process.env.NEXT_DIST_DIR || ".next",
};

export default nextConfig;
