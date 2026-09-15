/**
 * build.js – Bundle the Vibes frontend with Bun.
 *
 * Bundles all JS (app, components, api, preact-htm, katex, marked,
 * codemirror, beautiful-mermaid) into a single ESM file and all CSS
 * (KaTeX + pinned classic layers + Vibes adapters) into one stylesheet under static/dist/.
 *
 * Usage:  bun run build.js
 */

import { resolve, dirname, relative } from "path";
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from "fs";
import { fileURLToPath } from "url";
import { createHash } from 'node:crypto';

const __dirname = dirname(fileURLToPath(import.meta.url));
const staticDir = resolve(__dirname, "static");
const distDir = resolve(staticDir, "dist");

// ── JS bundle ─────────────────────────────────────────────────────────────
const planVendor = await Bun.build({entrypoints:[resolve(__dirname, 'plan-editor-vendor.js')], outdir:resolve(staticDir, 'js/vendor'), naming:'plan-codemirror.js', target:'browser', format:'esm', minify:true});
if (!planVendor.success) throw new Error(`Plan editor vendor build failed: ${planVendor.logs.join('\n')}`);
const jsResult = await Bun.build({
  entrypoints: [resolve(staticDir, "js/app.js")],
  outdir: distDir,
  format: "esm",
  minify: true,
  sourcemap: "external",
  target: "browser",
});

if (!jsResult.success) {
  console.error("JS build failed:");
  for (const msg of jsResult.logs) console.error(msg);
  process.exit(1);
}

for (const o of jsResult.outputs) {
  const rel = o.path.replace(staticDir + "/", "");
  console.log(`  ${rel}  ${(o.size / 1024).toFixed(1)} KB`);
}

// ── CSS bundle ────────────────────────────────────────────────────────────
// Concatenate all CSS sources then minify with bun's transpiler.
const cssSources = [
  resolve(staticDir, "css/katex.min.css"),
  // Preserve the deployed classic manifest order. Vibes adapters come last.
  ...["base", "shell", "workspace", "editor", "chat", "content", "agent", "overlays", "responsive", "settings"]
    .map(name => resolve(staticDir, `css/classic/${name}.css`)),
  resolve(staticDir, "css/styles.css"),
  resolve(staticDir, "css/plan-sidebar.css"),
];

const combined = cssSources
  .map((f) => readFileSync(f, "utf-8").replaceAll('../../common/fonts/', '../common/fonts/'))
  .join("\n");

// Bun doesn't have a CSS-only build API, so we do basic minification:
// collapse whitespace, strip comments, trim lines.
const minified = combined
  .replace(/\/\*[\s\S]*?\*\//g, "")   // strip block comments
  .replace(/\s*\n\s*/g, "\n")          // collapse around newlines
  .replace(/\n+/g, "\n")              // collapse multiple newlines
  .replace(/;\s*}/g, "}")             // drop last semicolon before }
  .replace(/\s*{\s*/g, "{")           // collapse around {
  .replace(/\s*}\s*/g, "}")           // collapse around }
  .replace(/\s*:\s*/g, ":")           // collapse around :
  .replace(/\s*;\s*/g, ";")           // collapse around ;
  .replace(/\s*,\s*/g, ",")           // collapse around ,
  .trim();

mkdirSync(distDir, { recursive: true });
const cssOut = resolve(distDir, "app.css");
writeFileSync(cssOut, minified, "utf-8");
const cssKb = (Buffer.byteLength(minified) / 1024).toFixed(1);
console.log(`  dist/app.css  ${cssKb} KB`);

const publicAssets = [];
function collectAssets(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = resolve(directory, entry.name);
    if (entry.isDirectory()) collectAssets(path);
    else if (/\.(js|mjs|css|png|svg|ttf|woff2|json)$/.test(entry.name)) {
      publicAssets.push(relative(staticDir, path).replaceAll('\\', '/'));
    }
  }
}
collectAssets(staticDir);
const shellAssets = ['/', '/static/js/bootstrap.js', '/static/dist/app.js?v=1', '/static/dist/app.css?v=1', '/static/extension-ui.js', '/static/frontend-sdk.js', '/static/widget-bridge.js'];
for (const asset of publicAssets) if (asset.endsWith('.woff2') || asset.startsWith('common/fonts/')) shellAssets.push(`/static/${asset}`);
const digest = createHash('sha256');
for (const path of shellAssets) {
    const name = path.split('?')[0];
    const source = name === '/' ? resolve(staticDir, 'index.html') : ['/static/extension-ui.js','/static/frontend-sdk.js','/static/widget-bridge.js'].includes(name) ? resolve(__dirname, '../static', name.slice(8)) : resolve(staticDir, name.slice(8));
    digest.update(path); digest.update(readFileSync(source));
}
const workerTemplate = readFileSync(resolve(__dirname, 'offline-worker.js'), 'utf8');
digest.update(workerTemplate);
writeFileSync(resolve(staticDir, 'offline-sw.js'), workerTemplate.replace('__TAU_SHELL__', JSON.stringify({version:digest.digest('hex').slice(0,20),assets:shellAssets})));
if (!publicAssets.includes('offline-sw.js')) publicAssets.push('offline-sw.js');
writeFileSync(resolve(__dirname, 'public-assets.json'), JSON.stringify(publicAssets.sort(), null, 2) + '\n');
console.log(`\nBuild complete.`);
