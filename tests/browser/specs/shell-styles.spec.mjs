import { expect, test } from '@playwright/test';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
const root = path.resolve(import.meta.dirname, '../../../src/tau_web/static');

// Reduced layout fixture following Piclaw App.tsx's container hierarchy.
// This tests CSS interference, not full-app reference/pixel approval.
test('compatibility CSS preserves Piclaw shell geometry', async ({ page }) => {
  await page.setContent(`<meta name="viewport" content="width=device-width, initial-scale=1"><div id="app"><div class="app-layout">
    <nav class="activity-bar"></nav><main class="app-layout__main">
      <div class="app-layout__content-area">
        <div class="app-layout__sidebar-wrapper"><aside class="sidebar"><header class="sidebar__header"><span class="sidebar__title">WORKSPACE</span></header><div class="sidebar__content">Shared workspace</div></aside></div>
        <div class="app-layout__panel"><div class="tab-bar">Chat</div><div class="app-layout__tab-viewport"><div class="app-layout__tab-content"><section class="chat"><div class="chat__messages">Shared message</div><div class="chat__compose"><textarea class="chat__input"></textarea></div></section></div></div></div>
      </div><div class="app-layout__status-bar">Shared status</div>
    </main></div></div>`);
  await page.addStyleTag({ content: await readFile(path.join(root, 'piclaw-reference.css'), 'utf8') });
  await page.addStyleTag({ content: '* { transition: none !important; animation: none !important; }' });
  const measure = () => page.locator('#app, #app *').evaluateAll(elements => elements.map(el => {
    const s = getComputedStyle(el), r = el.getBoundingClientRect();
    return { element: el.id || el.className, display: s.display, x: r.x, y: r.y, width: r.width, height: r.height };
  }));
  const upstream = await measure();
  await page.addStyleTag({ content: await readFile(path.join(root, 'piclaw-parity.css'), 'utf8') });
  expect(await measure()).toEqual(upstream);
});
