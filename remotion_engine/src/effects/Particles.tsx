// Particles.tsx
import React from "react";
import { useCurrentFrame } from "remotion";

export const ParticleEffect: React.FC<{ preset?: string; density?: string; speed?: number }> = ({ preset = "stars", density = "medium" }) => {
  const frame = useCurrentFrame();
  // Minimal placeholder: generate decorative dots
  const count = density === "low" ? 20 : density === "high" ? 80 : 40;
  const dots = new Array(count).fill(0).map((_, i) => {
    const x = (i * 47) % 100;
    const y = ((i * 73) + (frame % 100)) % 100;
    const size = (i % 6) + 1;
    return <div key={i} style={{ position: "absolute", left: `${x}%`, top: `${y}%`, width: size, height: size, borderRadius: size, background: "#fff", opacity: 0.5 }} />;
  });

  return <>{dots}</>;
};