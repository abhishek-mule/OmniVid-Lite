// LayerRenderer.tsx
import React from "react";
import { AbsoluteFill } from "remotion";
import { AnimatedText } from "./components/AnimatedText";
import { AnimatedImage } from "./components/AnimatedImage";
import { ParticleEffect } from "./effects/Particles";

export const LayerRenderer: React.FC<{ layer: any; scene: any; meta: any }> = ({ layer, scene, meta }) => {
  const type = layer.type;

  const commonProps = { layer, scene, meta };

  switch (type) {
    case "text":
      return <AnimatedText {...commonProps} />;
    case "image":
      return <AnimatedImage {...commonProps} />;
    case "particles":
      return <ParticleEffect preset={layer.preset || "stars"} density={layer.density || "medium"} />;
    case "shape":
      return <div /* TODO shape renderer */ />;
    default:
      return null;
  }
};