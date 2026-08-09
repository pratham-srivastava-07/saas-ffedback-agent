"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

/**
 * The product thesis rendered literally: scattered feedback resolving into
 * distinct themes.
 *
 * The points begin at uniform random positions and settle into clusters. That
 * is the one animation on the marketing page that carries meaning rather than
 * decoration, so it earns the WebGL cost. Everything else on the page is CSS.
 */

const POINT_COUNT = 1500;
const CLUSTER_COUNT = 6;
const SETTLE_SECONDS = 2.6;

/** Deterministic PRNG so the composition is identical on every load and in SSR. */
function mulberry32(seed: number) {
  return function next() {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

interface FieldData {
  scattered: Float32Array;
  clustered: Float32Array;
  colors: Float32Array;
  sizes: Float32Array;
}

function buildField(accent: THREE.Color, quiet: THREE.Color): FieldData {
  const random = mulberry32(20260810);
  const scattered = new Float32Array(POINT_COUNT * 3);
  const clustered = new Float32Array(POINT_COUNT * 3);
  const colors = new Float32Array(POINT_COUNT * 3);
  const sizes = new Float32Array(POINT_COUNT);

  const centres = Array.from({ length: CLUSTER_COUNT }, () => {
    const theta = random() * Math.PI * 2;
    const phi = Math.acos(2 * random() - 1);
    const radius = 1.5 + random() * 1.1;
    return new THREE.Vector3(
      radius * Math.sin(phi) * Math.cos(theta),
      radius * Math.sin(phi) * Math.sin(theta) * 0.62,
      radius * Math.cos(phi),
    );
  });

  // Two clusters carry the accent, standing in for the themes that matter.
  const accentClusters = new Set([0, 3]);
  const scratch = new THREE.Color();

  for (let i = 0; i < POINT_COUNT; i += 1) {
    const cluster = i % CLUSTER_COUNT;
    const centre = centres[cluster];

    // Uneven cluster tightness reads as real data rather than a lattice.
    const spread = 0.24 + (cluster % 3) * 0.11;
    const gx = (random() + random() + random() - 1.5) * spread;
    const gy = (random() + random() + random() - 1.5) * spread;
    const gz = (random() + random() + random() - 1.5) * spread;

    clustered[i * 3] = centre.x + gx;
    clustered[i * 3 + 1] = centre.y + gy;
    clustered[i * 3 + 2] = centre.z + gz;

    scattered[i * 3] = (random() - 0.5) * 9;
    scattered[i * 3 + 1] = (random() - 0.5) * 5.5;
    scattered[i * 3 + 2] = (random() - 0.5) * 9;

    const isAccent = accentClusters.has(cluster);
    scratch.copy(isAccent ? accent : quiet);
    // Slight per-point luminance variation stops the cloud reading as flat.
    scratch.multiplyScalar(0.72 + random() * 0.5);

    colors[i * 3] = scratch.r;
    colors[i * 3 + 1] = scratch.g;
    colors[i * 3 + 2] = scratch.b;

    sizes[i] = isAccent ? 0.032 + random() * 0.022 : 0.019 + random() * 0.016;
  }

  return { scattered, clustered, colors, sizes };
}

function Field({ reducedMotion }: { reducedMotion: boolean }) {
  const pointsRef = useRef<THREE.Points>(null);
  const groupRef = useRef<THREE.Group>(null);
  const elapsed = useRef(0);
  const pointer = useRef({ x: 0, y: 0 });

  const { scattered, clustered, colors, sizes } = useMemo(
    () =>
      buildField(
        new THREE.Color("#6d8bff"),
        new THREE.Color("#8b93ad"),
      ),
    [],
  );

  const positions = useMemo(
    () => (reducedMotion ? clustered.slice() : scattered.slice()),
    [reducedMotion, clustered, scattered],
  );

  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    geo.setAttribute("size", new THREE.BufferAttribute(sizes, 1));
    return geo;
  }, [positions, colors, sizes]);

  useFrame((state, delta) => {
    const group = groupRef.current;
    const points = pointsRef.current;
    if (!group || !points) return;

    if (reducedMotion) {
      // Static, resolved, readable. No drift, no settle.
      group.rotation.y = 0.35;
      return;
    }

    elapsed.current += delta;
    const progress = Math.min(elapsed.current / SETTLE_SECONDS, 1);
    // Ease-out cubic: fast commitment, gentle arrival.
    const eased = 1 - Math.pow(1 - progress, 3);

    if (progress < 1) {
      const attribute = points.geometry.getAttribute(
        "position",
      ) as THREE.BufferAttribute;
      const array = attribute.array as Float32Array;
      for (let i = 0; i < array.length; i += 1) {
        array[i] = scattered[i] + (clustered[i] - scattered[i]) * eased;
      }
      attribute.needsUpdate = true;
    }

    // Slow drift once settled, so the cloud stays alive without demanding
    // attention. Pointer parallax is read from a ref, never React state.
    group.rotation.y += delta * 0.055;
    group.rotation.x = THREE.MathUtils.lerp(
      group.rotation.x,
      pointer.current.y * 0.16,
      0.04,
    );
    group.position.x = THREE.MathUtils.lerp(
      group.position.x,
      pointer.current.x * 0.22,
      0.04,
    );

    const { pointer: statePointer } = state;
    pointer.current.x = statePointer.x;
    pointer.current.y = statePointer.y;
  });

  return (
    <group ref={groupRef}>
      <points ref={pointsRef} geometry={geometry}>
        <pointsMaterial
          vertexColors
          size={0.045}
          sizeAttenuation
          transparent
          opacity={0.95}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>
    </group>
  );
}

export default function PointField({
  reducedMotion = false,
}: {
  reducedMotion?: boolean;
}) {
  return (
    <Canvas
      camera={{ position: [0, 0, 6.2], fov: 46 }}
      dpr={[1, 1.75]}
      gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      // Nothing else on the page depends on this canvas, so pause it when the
      // tab is hidden rather than burning frames in the background.
      frameloop="always"
      style={{ pointerEvents: "none" }}
    >
      <Field reducedMotion={reducedMotion} />
    </Canvas>
  );
}
