import { expect, test } from '@playwright/test';

test('search results render through Piclaw search cards', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeVisible();
  await expect.poll(async () => (await page.locator('#app-status').textContent())?.trim() ?? '').not.toMatch(/Loading Tau shell/i);
  const cancel = page.getByRole('button', { name: 'Cancel' });
  await cancel.waitFor({ state: 'visible', timeout: 2000 }).catch(() => {});
  if (await cancel.isVisible()) await cancel.click();
  await page.evaluate(() => window.dispatchEvent(new CustomEvent('tau:search-render', { detail: { items: [
    { entityType: 'message', entityId: 'entry-1', meta: 'Session abc123 · Rank 1.25', text: 'Matching content', sessionId: 'session-1' },
  ] } })));
  await page.getByRole('button', { name: 'Search', exact: true }).first().click();
  const result = page.locator('#search-results .search-panel__item');
  await expect(result).toHaveCount(1);
  await expect(result.locator('.search-panel__item-type')).toHaveText('message · entry-1');
  await expect(result.locator('.search-panel__item-text')).toHaveText('Matching content');
  await expect(result.getByRole('button', { name: 'Open session' })).toBeVisible();
});
