// Generate a self-contained, labeled review document from existing captures.
// Usage: node build-visual-review.mjs [output.html]
import { readFile, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
const revision = execFileSync('git', ['rev-parse', 'HEAD'], {encoding:'utf8'}).trim();
const output = process.argv[2] ?? '/workspace/tmp/tau-visual-review.html';
const image = async file => `data:image/png;base64,${(await readFile(file)).toString('base64')}`;
const sections = [];
for (const engine of ['chromium','webkit']) for (const [viewport,size] of [['phone','390×844'],['tablet','820×1180'],['desktop','1440×900']]) for (const theme of ['light','dark']) {
  const key = `${engine}-${viewport}-${theme}`;
  const reference = await image(`/workspace/tmp/piclaw-full-reference/${key}.png`);
  const tau = await image(`/workspace/tmp/tau-populated-review/${key}-chat.png`);
  sections.push(`<section id="${key}"><h2>${engine} · ${size} · ${theme}</h2><div class="pair"><figure><figcaption>Piclaw 2.15.3 — genuine bundle, isolated fixture</figcaption><img src="${reference}" alt="Piclaw ${key}"></figure><figure><figcaption>Tau — shared content, selected review session</figcaption><img src="${tau}" alt="Tau ${key}"></figure></div></section>`);
}
await writeFile(output, `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Tau / Piclaw visual review</title><style>body{font:16px system-ui;margin:24px;background:#eee;color:#222}h1{margin-bottom:8px}.pair{display:flex;gap:16px;align-items:flex-start;overflow:auto}figure{margin:0;flex:1;min-width:360px}figcaption{font-weight:600;padding:8px}img{width:100%;height:auto;border:1px solid #999}section{margin:32px 0}code{overflow-wrap:anywhere}</style><h1>Tau / Piclaw — review, not acceptance</h1><p>Generator checkout: <code>${revision}</code>. Inputs are previously captured PNGs, not a new browser run. All twelve browser/viewport/theme pairs are included.</p><p>Both fixtures use connected synthetic transports and shared message content/model. Intentional or unresolved differences: identity/avatar; Tau's persistent Live indicator; session presentation; delivery/context controls; action inventory; scoped contrast fixes. Rich-renderer capabilities are not established by this sample. Settings/panels are not covered by these pairs.</p><p>Review layout, spacing, clipping, typography, message actions and composer placement at each size. Images are scaled to fit; open an image separately to inspect native pixels. No whole-image score or self-approved baseline is used.</p>${sections.join('\n')}</html>`);
console.log(output);
