"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

/**
 * Guards every WebGL surface in the app.
 *
 * three.js is a large dependency, so it is dynamically imported and never
 * enters the initial bundle. The page must remain complete without it: if the
 * device cannot do WebGL the fallback is the design, not an error.
 */

import type { ClusterScatterProps } from "@/components/three/cluster-scatter";

const PointField = dynamic(() => import("@/components/three/point-field"), {
  ssr: false,
  loading: () => null,
});

const ClusterScatter = dynamic(
  () => import("@/components/three/cluster-scatter"),
  { ssr: false, loading: () => null },
);

function supportsWebGL(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const canvas = document.createElement("canvas");
    return Boolean(
      window.WebGLRenderingContext &&
        (canvas.getContext("webgl") || canvas.getContext("experimental-webgl")),
    );
  } catch {
    return false;
  }
}

export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(query.matches);
    const listener = (event: MediaQueryListEvent) => setReduced(event.matches);
    query.addEventListener("change", listener);
    return () => query.removeEventListener("change", listener);
  }, []);

  return reduced;
}

export function HeroField({ className }: { className?: string }) {
  const [ready, setReady] = useState(false);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    setReady(supportsWebGL());
  }, []);

  if (!ready) {
    // Nothing. The previous fallback was two stacked radial gradients standing
    // in for the point cloud, which is the decorative-orb pattern the frontend
    // rules ban outright. A hero that needs a coloured blur behind it to look
    // finished is not finished; the type and the layout carry it, and a device
    // without WebGL simply gets the page without the ornament.
    return null;
  }

  return (
    <div className={className} aria-hidden>
      <PointField reducedMotion={reducedMotion} />
    </div>
  );
}

/**
 * The cluster explorer's canvas.
 *
 * Unlike the hero, this one carries information, so a device without WebGL
 * cannot simply be given a gradient — the caller supplies a fallback, and the
 * page keeps a readable list of the same data either way.
 */
export function ScatterField({
  className,
  fallback,
  ...props
}: Omit<ClusterScatterProps, "reducedMotion"> & {
  className?: string;
  fallback: React.ReactNode;
}) {
  const [ready, setReady] = useState(false);
  const [checked, setChecked] = useState(false);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    setReady(supportsWebGL());
    setChecked(true);
  }, []);

  if (!checked) return <div className={className} />;
  if (!ready) return <div className={className}>{fallback}</div>;

  return (
    <div className={className}>
      <ClusterScatter {...props} reducedMotion={reducedMotion} />
    </div>
  );
}
