import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export const SceneText = ({ content, color = "black", fontSize = 80 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Simple fade-in animation
  const opacity = interpolate(frame, [0, fps], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        color,
        fontSize,
        opacity,
      }}
    >
      {content}
    </AbsoluteFill>
  );
};