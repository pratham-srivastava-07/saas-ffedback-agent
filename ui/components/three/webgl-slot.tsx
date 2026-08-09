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

const PointField = dynamic(() => import("@/components/three/point-field"), {
  ssr: false,
  loading: () => null,
});

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
    // Deliberate, not a placeholder: a soft field that echoes the cloud's
    // composition so the hero still has depth without a GPU.
    return (
      <div
        className={className}
        aria-hidden
        style={{
          background:
            "radial-gradient(38rem 24rem at 68% 42%, oklch(0.55 0.19 264 / 0.20), transparent 70%), radial-gradient(26rem 18rem at 82% 68%, oklch(0.6 0.1 250 / 0.14), transparent 72%)",
        }}
      />
    );
  }

  return (
    <div className={className} aria-hidden>
      <PointField reducedMotion={reducedMotion} />
    </div>
  );
}
