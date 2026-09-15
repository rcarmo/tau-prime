import { expect, test } from '@playwright/test';

test.use({ serviceWorkers: 'allow' });

async function verifyCache(page) {
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready', 'true');
  await page.evaluate(async () => { await navigator.serviceWorker.ready; });
  await expect.poll(() => page.evaluate(() => Boolean(navigator.serviceWorker.controller))).toBe(true);
  const cached = await page.evaluate(async () => {
    const cache = await caches.open('tau-web-shell-v12');
    return (await cache.keys()).map(request => new URL(request.url).pathname);
  });
  expect(cached).toContain('/');
  expect(cached).toContain('/static/preact-shell.js');
  const unusable = await page.evaluate(async () => {
    const cache = await caches.open('tau-web-shell-v12');
    const failures = [];
    for (const request of await cache.keys()) {
      const response = await cache.match(request);
      if (!response?.ok || !(await response.arrayBuffer()).byteLength) failures.push(request.url);
    }
    return failures;
  });
  expect(unusable).toEqual([]);
  expect(cached.filter(name => /\.(woff2|ttf)$/.test(name))).toHaveLength(2);
  expect(cached).toContain('/static/piclaw-classic.css');
  expect(cached).toContain('/static/tau-classic.css');
  expect(cached.some(name => /piclaw-reference|piclaw-parity|JetBrains/.test(name))).toBe(false);
  expect(cached.some(name => name.startsWith('/api/'))).toBe(false);
}

test('service worker caches shell assets without API data', async ({ page }) => {
  await verifyCache(page);
});

test('service worker supports offline reload', async ({ page, context, browserName }) => {
  test.skip(browserName === 'webkit' && process.env.TAU_PROBE_WEBKIT_OFFLINE !== '1', 'WebKit offline navigation reports internal browser error; set TAU_PROBE_WEBKIT_OFFLINE=1 to reproduce.');
  await verifyCache(page);
  await context.setOffline(true);
  try {
    await page.reload({ waitUntil: 'domcontentloaded' });
    await expect(page.locator('#compose-input')).toBeVisible();
    await expect(page.locator('.app-shell')).toBeVisible();
    await expect(page.locator('.activity-bar')).toHaveCount(0);
  } finally {
    await context.setOffline(false);
  }
});
