import { build } from "esbuild";
import { join } from "node:path";

const frontendRoot = import.meta.dir;
const outfile = join(frontendRoot, "..", "static", "preact-shell.js");

await build({
  absWorkingDir: frontendRoot,
  bundle: true,
  entryPoints: ["src/index.tsx"],
  format: "esm",
  jsx: "automatic",
  jsxImportSource: "preact",
  legalComments: "none",
  outfile,
  platform: "browser",
  target: ["es2022"],
});

console.log(`wrote ${outfile}`);
