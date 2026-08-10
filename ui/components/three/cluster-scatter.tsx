"use client";

import { useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";

import type { ScatterPoint } from "@/lib/api";
import { colorForTheme } from "@/lib/cluster-colors";

/**
 * The embedding space, projected.
 *
 * Every coordinate here is a real PCA projection of the feedback's embedding —
 * nothing is generated for looks. Two consequences the UI has to respect:
 *
 * 1. PCA is fit per run, so two runs have different bases. Coordinates are
 *    never comparable across runs and must never be animated between them.
 * 2. The axes are principal components. They carry no nameable meaning, so
 *    they are left unlabelled — only the *distances* between points are
 *    interpretable.
 *
 * A run is capped at 200 items, so each point is its own mesh. That keeps
 * click handling exact instead of fighting raycaster thresholds on a
 * buffer-geometry point cloud.
 */

export interface ClusterScatterProps {
  points: ScatterPoint[];
  /** Theme ids in display order; fixes each cluster's colour. */
  themeOrder: string[];
  selectedId: string | null;
  onSelect: (point: ScatterPoint | null) => void;
  /** When set, everything outside this theme fades back. */
  focusThemeId: string | null;
  reducedMotion?: boolean;
}

function Dot({
  point,
  color,
  selected,
  dimmed,
  onSelect,
}: {
  point: ScatterPoint;
  color: string;
  selected: boolean;
  dimmed: boolean;
  onSelect: (point: ScatterPoint) => void;
}) {
  const [hovered, setHovered] = useState(false);
  const emphasis = selected || hovered;

  return (
    <mesh
      position={[point.x, point.y, point.z]}
      scale={selected ? 2.2 : hovered ? 1.7 : 1}
      onClick={(event) => {
        event.stopPropagation();
        onSelect(point);
      }}
      onPointerOver={(event) => {
        event.stopPropagation();
        setHovered(true);
        document.body.style.cursor = "pointer";
      }}
      onPointerOut={() => {
        setHovered(false);
        document.body.style.cursor = "";
      }}
    >
      <sphereGeometry args={[0.022, 16, 16]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={emphasis ? 0.75 : 0.2}
        transparent
        opacity={dimmed ? 0.15 : 1}
        roughness={0.45}
      />
    </mesh>
  );
}

export default function ClusterScatter({
  points,
  themeOrder,
  selectedId,
  onSelect,
  focusThemeId,
  reducedMotion = false,
}: ClusterScatterProps) {
  return (
    <Canvas
      camera={{ position: [2.4, 1.7, 2.4], fov: 45 }}
      dpr={[1, 2]}
      // Clicking empty space clears the selection, which is what people expect
      // and avoids trapping them in a detail panel.
      onPointerMissed={() => onSelect(null)}
    >
      <ambientLight intensity={0.9} />
      <directionalLight position={[3, 4, 2]} intensity={0.55} />

      {points.map((point) => (
        <Dot
          key={point.item_id}
          point={point}
          color={colorForTheme(point.theme_id, themeOrder)}
          selected={point.item_id === selectedId}
          dimmed={Boolean(focusThemeId) && point.theme_id !== focusThemeId}
          onSelect={onSelect}
        />
      ))}

      <OrbitControls
        enablePan={false}
        enableDamping
        // Idle rotation reads as "alive"; it stops the moment someone is
        // actually reading a point, and never runs under reduced motion.
        autoRotate={!reducedMotion && !selectedId}
        autoRotateSpeed={0.45}
        minDistance={1.1}
        maxDistance={7}
      />
    </Canvas>
  );
}
