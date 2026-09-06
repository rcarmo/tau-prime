import { expect, test } from '@playwright/test';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

const frontend = path.resolve(import.meta.dirname, '../../../src/tau_web/frontend');
const require = createRequire(path.join(frontend, 'package.json'));
const { build } = require('esbuild');
const reference = process.env.PICLAW_VISUAL_SOURCE || '/opt/piclaw/releases/piclaw-2.15.3-linux-x64-baseline/app/runtime/web/static/visual/frontend/src';

test('single-chat tab matches actual Piclaw component markup and computed styles', async ({ page }) => {
  // Compile the genuine upstream component, not a Tau-generated reference.
  const result = await build({
    stdin: { contents: `import {render} from 'preact';
      import {TabBar as Reference} from ${JSON.stringify(path.join(reference, 'components/TabBar.tsx'))};
      import {TabBar as Tau} from ${JSON.stringify(path.join(frontend, 'src/components/TabBar.tsx'))};
      render(<Reference tabs={[{id:'chat',label:'Chat'}]} activeTabId="chat" onSelectTab={()=>{}} onCloseTab={()=>{}} />,document.getElementById('reference'));
      render(<Tau />,document.getElementById('tau'));`, loader: 'tsx', resolveDir: frontend },
    bundle: true, write: false, format: 'iife', jsx: 'automatic', jsxImportSource: 'preact',
    nodePaths: [path.join(frontend, 'node_modules')],
  });
  await page.setContent('<meta name="viewport" content="width=device-width, initial-scale=1"><div id="reference"></div><div id="tau"></div>');
  await page.addStyleTag({ content: await readFile(path.join(frontend, '../static/piclaw-reference.css'), 'utf8') });
  await page.addScriptTag({ content: result.outputFiles[0].text });
  const measure = selector => page.locator(selector).evaluate(root => ({
    html: root.innerHTML,
    elements: [...root.querySelectorAll('*')].map(el => {
      const s = getComputedStyle(el);
      return Object.fromEntries(['height','fontFamily','fontSize','fontWeight','color','backgroundColor','padding','border','display','gap'].map(k => [k,s[k]]));
    }),
  }));
  const upstream = await measure('#reference');
  expect(await measure('#tau')).toEqual(upstream);
  await page.addStyleTag({ content: await readFile(path.join(frontend, '../static/piclaw-parity.css'), 'utf8') });
  // Tau's compatibility sheet must not alter the upstream tab's appearance.
  expect(await measure('#tau')).toEqual(upstream);
});
