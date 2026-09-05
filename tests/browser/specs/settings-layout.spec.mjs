import { expect, test } from '@playwright/test';

test('settings occupies central pane without remounting Tau API form anchors', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeAttached();
  await expect.poll(async () => (await page.locator('#app-status').textContent())?.trim() ?? '').not.toMatch(/Loading Tau shell/i);
  const cancel = page.getByRole('button', { name: 'Cancel', exact: true });
  if (await cancel.isVisible()) await cancel.click();
  await page.evaluate(() => { window.__authAnchor = document.getElementById('auth-form'); });
  const settings = page.getByRole('button', { name: 'Settings', exact: true });
  await settings.click();
  await expect(page.locator('.app-layout__panel > #panel-settings')).toBeVisible();
  await expect(page.locator('.app-layout__sidebar-wrapper')).toBeHidden();
  await expect(page.locator('#compose-input')).toBeHidden();
  await expect(page.locator('#auth-token')).toBeVisible();
  await settings.click();
  await expect(page.locator('#panel-settings')).toBeHidden();
  await expect(page.locator('#compose-input')).toBeVisible();
  expect(await page.evaluate(() => window.__authAnchor === document.getElementById('auth-form'))).toBe(true);
});
