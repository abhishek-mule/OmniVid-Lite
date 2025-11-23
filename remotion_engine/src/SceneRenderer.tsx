// SceneRenderer.tsx
import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { LayerRenderer } from "./LayerRenderer";
import { renderBackgroundStyle } from "./helpers";

export const SceneRenderer: React.FC<{ scene: any; meta: any; sceneIndex: number }> = ({ scene, meta, sceneIndex }) => {
  const fps = meta.fps || 30;
  const duration = scene.duration || Math.floor(3 * fps);
  const fromFrame = scene.startFrame ?? 0; // handled by MainVideo/Sequence offsets

  return (
    <Sequence from={fromFrame} durationInFrames={duration}>
      <AbsoluteFill style={renderBackgroundStyle(scene.background, meta)}>
        {scene.layers?.map((layer: any, i: number) => (
          <LayerRenderer key={`${scene.id}-${layer.id || i}`} layer={layer} scene={scene} meta={meta} />
        ))}
        {/* Additional scene overlays / debug */}
      </AbsoluteFill>
    </Sequence>
  );
};

export default SceneRenderer;