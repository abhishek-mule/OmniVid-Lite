import { registerRoot } from "remotion";
import { Composition } from "remotion";
import { MainVideo } from "./MainVideo";
import { default as GeneratedScene } from "./generated/direct_test_job/GeneratedScene";

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

  compositions.push(
    <Composition
      key="GeneratedScene"
      id="GeneratedScene"
      component={GeneratedScene}
      width={1920}
      height={1080}
      fps={30}
      durationInFrames={30 * 5}
      defaultProps={{}}
    />
  );
  return <>{compositions}</>;
};

registerRoot(RemotionRoot);
