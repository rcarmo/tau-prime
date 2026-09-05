import { expect, test } from '@playwright/test';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
const root = path.resolve(import.meta.dirname, '../../../src/tau_web/static');

test('compatibility CSS preserves standard Piclaw control styles', async ({ page }) => {
  await page.setContent(`<main>
    <button class="provider-wizard__btn provider-wizard__btn--primary">Connect</button>
    <button class="modal-dialog__btn modal-dialog__btn--primary">Confirm</button>
    <button class="chat__send-btn">Send</button>
    <input class="settings-panel__input" value="Model" />
    <textarea class="chat__input">Message</textarea>
    <select class="settings-panel__select"><option>Provider</option></select>
  </main>`);
  await page.addStyleTag({ content: await readFile(path.join(root, 'piclaw-reference.css'), 'utf8') });
  // Eliminate transition interpolation, not visual styles, from measurements.
  await page.addStyleTag({ content: '* { transition: none !important; animation: none !important; }' });
  const measure = () => page.locator('main > *').evaluateAll(elements => elements.map(el => {
    const s = getComputedStyle(el);
    return { component: el.className, ...Object.fromEntries(['color','backgroundColor','borderColor','webkitTextFillColor','fontFamily','fontSize','padding','height'].map(k => [k, s[k]])) };
  }));
  const upstream = await measure();
  await page.addStyleTag({ content: await readFile(path.join(root, 'piclaw-parity.css'), 'utf8') });
  expect(await measure()).toEqual(upstream);
});
