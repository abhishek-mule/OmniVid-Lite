import { registerRoot } from "remotion";
import { Composition } from "remotion";
import { MainVideo } from "./MainVideo";

export const RemotionRoot: React.FC = () => {
  const compositions = [];

  // Add static Main composition for development
  compositions.push(
    <Composition
      key="Main"
      id="Main"
      component={MainVideo}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={30 * 5}
      defaultProps={{
        config: {
          width: 1080,
          height: 1920,
          fps: 30,
          durationInSeconds: 5,
          scenes: [],
        },
      }}
    />
  );

  // Note: Dynamic compositions are registered at runtime via the adapter
  // The generated/index.ts file is built dynamically during the pipeline

  return <>{compositions}</>;
};

registerRoot(RemotionRoot);
