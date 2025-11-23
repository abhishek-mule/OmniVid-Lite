// MotionEngine.tsx
import React from "react";
import { AbsoluteFill } from "remotion";
import { SceneRenderer } from "./SceneRenderer";

export const MotionEngine: React.FC<{ dsl: any }> = ({ dsl }) => {
  const meta = dsl.meta || { fps: 30, width: 1920, height: 1080 };
  const scenes = dsl.scenes || [];

  return (
    <AbsoluteFill style={{ width: meta.width, height: meta.height }}>
      {scenes.map((scene: any, idx: number) => (
        <SceneRenderer key={scene.id || idx} scene={scene} meta={meta} sceneIndex={idx} />
      ))}
    </AbsoluteFill>
  );
};

export default MotionEngine;