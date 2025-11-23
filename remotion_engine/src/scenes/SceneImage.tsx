import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export const SceneImage = ({ src, scale = 1 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const animScale = interpolate(frame, [0, fps], [0.8 * scale, 1 * scale], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <Img
        src={src}
        style={{
          width: "70%",
          transform: `scale(${animScale})`,
        }}
      />
    </AbsoluteFill>
  );
};