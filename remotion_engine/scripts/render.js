const { bundle } = require("@remotion/bundler");
const { renderMedia } = require("@remotion/renderer");
const path = require("path");
const minimist = require("minimist");
const fs = require("fs");

// Read CLI args
const args = minimist(process.argv.slice(2));
const configPath = args.config;
const outPath = args.out || "out/output.mp4";

if (!configPath) {
  console.error("❌ Error: Use --config=<path-to-json>");
  process.exit(1);
}

// Parse animation config JSON
const fullPath = path.resolve(configPath);
if (!fs.existsSync(fullPath)) {
  console.error("❌ Config file not found:", fullPath);
  process.exit(1);
}

const animationConfig = JSON.parse(fs.readFileSync(fullPath, "utf-8"));

async function run() {
  console.log("📦 Bundling Remotion project...");
  const entry = path.join(process.cwd(), "src", "index.tsx");
  const bundleLocation = await bundle(entry);

  console.log("🎬 Rendering video...");
  await renderMedia({
    composition: "Main",
    serveUrl: bundleLocation,
    codec: "h264",
    outputLocation: outPath,
    inputProps: {
      config: animationConfig, // Pass JSON to Remotion
    },
  });

  console.log("✅ Finished! Saved to", outPath);
}

run();