import { registerRoot } from "remotion";
import { Composition } from "remotion";
import { MainVideo } from "./MainVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={MainVideo}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={30 * 5} // temporary, replaced by inputProps during render
      defaultProps={{
        config: {
          width: 1080,
          height: 1920,
          fps: 30,
          durationInSeconds: 5,
          scenes: [
            // Dev-only sample (removed in real render)
          ],
        },
      }}
    />
  );
};

registerRoot(RemotionRoot);
