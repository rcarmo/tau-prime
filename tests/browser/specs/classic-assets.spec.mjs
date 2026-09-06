import { expect, test } from '@playwright/test';
import { installSelectedSession } from '../fixtures/selected-session.mjs';
import { installLiveStream } from '../fixtures/live-stream.mjs';

test('classic fonts and SVG controls load without rejected visual assets', async ({ page, request }) => {
  await installSelectedSession(page);
  await installLiveStream(page, 'tau');
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready', 'true');
  const cancel = page.getByRole('button', { name: 'Cancel', exact: true });
  if (await cancel.isVisible()) await cancel.click();
  const fonts = await page.evaluate(async () => {
    const css = await (await fetch('/static/piclaw-classic.css')).text();
    const names = [...new Set([...css.matchAll(/url\(\.\/([^)]*)\)/g)].map(match => match[1]))];
    return Promise.all(names.map(async (name, index) => {
      const response = await fetch(`/static/${name}`);
      const face = new FontFace(`ClassicFixture${index}`, `url(/static/${name})`);
      await face.load();
      return {name, status: response.status, loaded: face.status};
    }));
  });
  expect(fonts).toHaveLength(2);
  for (const font of fonts) {
    expect(font.name).toMatch(/^firacode-.*\.ttf$/);
    expect(font.status).toBe(200);
    expect(font.loaded).toBe('loaded');
  }
  await expect(page.locator('#compose-attachment-button svg')).toBeVisible();
  await expect(page.locator('#compose-submit svg')).toBeVisible();
  await expect(page.locator('link[href*="piclaw-reference"],link[href*="piclaw-parity"]')).toHaveCount(0);
  for (const name of ['piclaw-reference.css', 'piclaw-parity.css', 'JetBrainsMonoNFM-Medium-hh38vnv1.woff2', 'JetBrainsMonoNFM-Regular-rhdb9m6d.woff2']) {
    expect((await request.get(`/static/${name}`)).status()).toBe(404);
  }
  expect(errors).toEqual([]);
});
