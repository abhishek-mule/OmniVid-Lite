// AnimatedImage.tsx
import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { Img } from "remotion";

export const AnimatedImage: React.FC<{ layer: any; scene: any; meta: any }> = ({ layer }) => {
  const frame = useCurrentFrame();
  const inSpec = layer.animation?.in;
  const left = typeof layer.position === "object" ? layer.position.x : (layer.position === "center" ? "50%" : layer.position ?? 0);
  const top = typeof layer.position === "object" ? layer.position.y : (layer.position === "center" ? "50%" : layer.position ?? 0);
  const translateCenter = layer.position === "center" ? "translate(-50%,-50%)" : "";

  let scale = layer.style?.scale ?? 1;
  if (inSpec?.type === "slide-up") {
    const prog = interpolate(frame, [inSpec.startFrame ?? 0, (inSpec.startFrame ?? 0) + (inSpec.duration ?? 20)], [50, 0], { extrapolateRight: "clamp" });
    return (
      <AbsoluteFill style={{ position: "absolute", left, top, transform: `${translateCenter} translateY(${prog}px)`, display: "flex", justifyContent: "center", alignItems: "center" }}>
        <Img src={layer.url || layer.src} style={{ width: layer.style?.width || "50%", borderRadius: layer.style?.borderRadius || 8, transform: `scale(${scale})` }} />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ position: "absolute", left, top, transform: translateCenter, display: "flex", justifyContent: "center", alignItems: "center" }}>
      <Img src={layer.url || layer.src} style={{ width: layer.style?.width || "50%", borderRadius: layer.style?.borderRadius || 8, transform: `scale(${scale})` }} />
    </AbsoluteFill>
  );
};