import { expect, test } from '@playwright/test';

test('system meters render Tau snapshots through Piclaw stats markup', async ({ page }) => {
  const snapshot = {
    cpu_percent: 92, ram_percent: 64, process_rss_bytes: 5242880, swap_percent: 2,
    cpu_series: [20, 50, 92], ram_series: [55, 60, 64], process_rss_series_bytes: [1048576, 3145728, 5242880], swap_series: [0, 1, 2],
  };
  await page.addInitScript(() => {
    window.EventSource = class { close() {} };
    window.localStorage.setItem('tau.web.metersCollapsed', 'false');
  });
  await page.route('**/meters', (route) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(snapshot) }));
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeVisible();
  await expect.poll(async () => (await page.locator('#app-status').textContent())?.trim() ?? '').not.toMatch(/Loading Tau shell/i);
  await page.evaluate((meters) => window.dispatchEvent(new CustomEvent('tau:meters-render', { detail: {
    enabled: true, collapsed: false, meters,
  } })), snapshot);

  const meters = page.locator('#system-meters');
  await expect(meters).toHaveAttribute('data-collapsed', 'false');
  await expect(page.locator('#meters-summary')).toHaveText('CPU 92% · RAM 64% · RSS 5.0 MB · Swap 2%');
  await expect(page.locator('#meter-cpu-value')).toHaveClass(/sys-stats__value--error/);
  await expect(page.locator('#meter-ram-value')).toHaveClass(/sys-stats__value--warning/);
  await expect(page.locator('#meter-swap-value')).toHaveClass(/sys-stats__value--warning/);
  await expect(page.locator('#meter-cpu-sparkline polyline')).toHaveCount(1);
});
