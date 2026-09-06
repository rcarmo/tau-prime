import { expect, test } from '@playwright/test';

test.use({ serviceWorkers: 'allow' });

async function verifyCache(page) {
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready', 'true');
  await page.evaluate(async () => { await navigator.serviceWorker.ready; });
  await expect.poll(() => page.evaluate(() => Boolean(navigator.serviceWorker.controller))).toBe(true);
  const cached = await page.evaluate(async () => {
    const cache = await caches.open('tau-web-shell-v11');
    return (await cache.keys()).map(request => new URL(request.url).pathname);
  });
  expect(cached).toContain('/static/preact-shell.js');
  expect(cached.filter(name => /\.(woff2|ttf)$/.test(name))).toHaveLength(4);
  expect(cached.some(name => name.startsWith('/api/'))).toBe(false);
}

test('service worker caches shell assets without API data', async ({ page }) => {
  await verifyCache(page);
});

test('service worker supports offline reload', async ({ page, context, browserName }) => {
  test.skip(browserName === 'webkit', 'WebKit offline navigation reports internal browser error; cache verification runs separately.');
  await verifyCache(page);
  await context.setOffline(true);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(page.locator('#compose-input')).toBeVisible();
  await expect(page.locator('.activity-bar')).toBeVisible();
  await context.setOffline(false);
});
