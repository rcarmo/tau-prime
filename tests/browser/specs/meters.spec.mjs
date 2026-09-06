import { expect, test } from '@playwright/test';
import { installLiveStream } from '../fixtures/live-stream.mjs';

test('system meters render Tau snapshots through Piclaw stats markup', async ({ page }) => {
  const snapshot = {
    cpu_percent: 92, ram_percent: 64, process_rss_bytes: 5242880, swap_percent: 2,
    cpu_series: [20, 50, 92], ram_series: [55, 60, 64], process_rss_series_bytes: [1048576, 3145728, 5242880], swap_series: [0, 1, 2],
  };
  await installLiveStream(page, 'tau');
  await page.addInitScript(() => {
    window.localStorage.setItem('tau.web.metersCollapsed', 'false');
  });
  await page.route('**/meters', (route) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(snapshot) }));
  await page.goto('/', {waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready', 'true');
  await page.evaluate((meters) => window.dispatchEvent(new CustomEvent('tau:meters-render', { detail: {
    enabled: true, collapsed: false, meters,
  } })), snapshot);

  const meters = page.locator('#system-meters');
  await expect(meters).toHaveAttribute('data-collapsed', 'false');
  await expect(page.locator('#meters-summary')).toHaveText('CPU 92% · RAM 64% · RSS 5.0 MB · Swap 2%');
  await expect(page.locator('#meter-cpu-value')).toHaveClass(/tau-metric-value--error/);
  await expect(page.locator('#meter-ram-value')).toHaveClass(/tau-metric-value--warning/);
  await expect(page.locator('#meter-swap-value')).toHaveClass(/tau-metric-value--warning/);
  await expect(page.locator('#meter-cpu-sparkline polyline')).toHaveCount(1);
  const cancel=page.getByRole('button',{name:'Cancel',exact:true});await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});if(await cancel.isVisible())await cancel.click();
  await page.getByRole('button',{name:'Open sessions',exact:true}).click();
  await expect(page.locator('#meters-details')).toBeVisible();
  await page.getByRole('button',{name:'Compact meters',exact:true}).click();
  await expect(page.locator('#meters-details')).toBeHidden();
  await expect(page.locator('#meters-summary')).toBeVisible();
  await page.getByRole('button',{name:'Hide meters',exact:true}).click();
  await expect(page.locator('#meters-summary')).toBeHidden();
  await page.getByRole('button',{name:'Show meters',exact:true}).click();
  await page.getByRole('button',{name:'Expand meters',exact:true}).click();
  await expect(page.locator('#meters-details')).toBeVisible();
  await expect(meters.locator('.codicon')).toHaveCount(0);
});
