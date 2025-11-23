// AnimatedText.tsx
import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";

export const AnimatedText: React.FC<{ layer: any; scene: any; meta: any }> = ({ layer }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const style = layer.style || {};
  const anim = layer.animation || {};
  const inSpec = anim.in;
  const outSpec = anim.out;

  // default position center or explicit coords
  const position = layer.position || "center";
  const left = position === "center" ? "50%" : layer.position?.x ?? 0;
  const top = position === "center" ? "50%" : layer.position?.y ?? 0;
  const translateCenter = position === "center" ? "translate(-50%,-50%)" : "";

  // scale animation example: zoom-in uses spring for elasticity
  let scale = 1;
  if (inSpec?.type === "zoom-in") {
    if (inSpec.easing === "spring") {
      scale = spring({ frame, fps, config: { damping: 10, stiffness: 120 } }) * (layer.style?.scale ?? 1);
    } else {
      const prog = interpolate(frame, [inSpec.startFrame ?? 0, (inSpec.startFrame ?? 0) + (inSpec.duration ?? 20)], [0.7, 1], { extrapolateRight: "clamp" });
      scale = prog;
    }
  }

  // opacity example
  let opacity = 1;
  if (inSpec?.type?.includes("fade") || inSpec?.type === "fade-up") {
    const prog = interpolate(frame, [inSpec.startFrame ?? 0, (inSpec.startFrame ?? 0) + (inSpec.duration ?? 20)], [0, 1], { extrapolateRight: "clamp" });
    opacity = prog;
  }

  return (
    <AbsoluteFill style={{
      position: "absolute",
      left,
      top,
      transform: `${translateCenter} scale(${scale})`,
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      pointerEvents: "none",
      opacity
    }}>
      <div style={{
        color: style.color || "#fff",
        fontSize: style.size || 60,
        fontWeight: style.weight || 700,
        letterSpacing: (style.tracking ?? 0) + "px",
        fontFamily: style.font || "Inter, sans-serif",
        textAlign: "center"
      }}>
        {layer.content}
      </div>
    </AbsoluteFill>
  );
};