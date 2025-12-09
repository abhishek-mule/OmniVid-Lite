const { bundle } = require("@remotion/bundler");
const { renderMedia } = require("@remotion/renderer");
const path = require("path");
const minimist = require("minimist");
const fs = require("fs");

// Read CLI args
const args = minimist(process.argv.slice(2));
const compId = args.comp || "Main";
const configPath = args.config;
const outPath = args.out || "out/output.mp4";

if (!configPath && !args.comp) {
  console.error("❌ Error: Provide either --config=<path.json> or --comp=<compositionId>");
  process.exit(1);
}

let animationConfig = null;
if (configPath) {
  // Parse animation config JSON
  const fullPath = path.resolve(configPath);
  if (!fs.existsSync(fullPath)) {
    console.error("❌ Config file not found:", fullPath);
    process.exit(1);
  }
  animationConfig = JSON.parse(fs.readFileSync(fullPath, "utf-8"));
}

async function run() {
  console.log("📦 Bundling Remotion project...");
  const entry = path.join(process.cwd(), "src", "index.tsx");
  const bundleLocation = await bundle(entry);

  console.log("🎬 Rendering video...");
  const renderOptions = {
    composition: compId,
    serveUrl: bundleLocation,
    codec: "h264",
    outputLocation: outPath,
  };
  if (animationConfig) {
    renderOptions.inputProps = { config: animationConfig };
  }
  await renderMedia(renderOptions);

  console.log("✅ Finished! Saved to", outPath);
}

run();