import { expect, test } from '@playwright/test';
import { readFile } from 'node:fs/promises';
import path from 'node:path';

const staticRoot = path.resolve(import.meta.dirname, '../../../src/tau_web/static');

test('Tau compatibility sheet preserves Piclaw root theme tokens', async ({ page }) => {
  await page.setContent('<meta name="viewport" content="width=device-width, initial-scale=1"><main>Theme fixture</main>');
  await page.addStyleTag({ content: await readFile(path.join(staticRoot, 'piclaw-classic.css'), 'utf8') });
  const tokens = await page.evaluate(() => {
    const style = getComputedStyle(document.documentElement);
    return Object.fromEntries([...style].filter(k => k.startsWith('--')).map(k => [k, style.getPropertyValue(k).trim()]));
  });
  expect(Object.keys(tokens).length).toBeGreaterThan(20);
  await page.addStyleTag({ content: await readFile(path.join(staticRoot, 'tau-classic.css'), 'utf8') });
  const changed = await page.evaluate(before => {
    const after = getComputedStyle(document.documentElement);
    return Object.entries(before).filter(([key, value]) => after.getPropertyValue(key).trim() !== value)
      .map(([key, value]) => ({ key, before: value, after: after.getPropertyValue(key).trim() }));
  }, tokens);
  expect(changed).toEqual([]);
});
