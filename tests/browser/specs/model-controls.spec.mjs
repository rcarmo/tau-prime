import { expect, test } from '@playwright/test';

test('model and thinking options are Preact-owned', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeVisible();
  const cancel = page.getByRole('button', { name: 'Cancel' });
  await cancel.waitFor({ state: 'visible', timeout: 2000 }).catch(() => {});
  if (await cancel.isVisible()) await cancel.click();
  await page.evaluate(() => {
    window.dispatchEvent(new CustomEvent('tau:model-options-render', { detail: {
      providers: [{ value: 'anthropic', label: 'Anthropic' }],
      models: [{ value: 'claude', label: 'Claude' }],
    } }));
    window.dispatchEvent(new CustomEvent('tau:thinking-options-render', { detail: { items: [
      { value: '', label: 'Default' }, { value: 'high', label: 'High' },
    ] } }));
  });
  await expect(page.locator('#compose-provider-select option')).toHaveCount(1);
  await expect(page.locator('#compose-model-select option')).toHaveText(['Claude']);
  await expect(page.locator('#compose-thinking-select option')).toHaveCount(2);
  await page.getByRole('button', { name: 'Settings', exact: true }).first().click();
  await expect(page.locator('#provider-options option')).toHaveAttribute('value', 'anthropic');
  await expect(page.locator('#thinking-level-select option')).toHaveCount(7);
});
