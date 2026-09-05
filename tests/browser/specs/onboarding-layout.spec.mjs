import { expect, test } from '@playwright/test';

test('provider setup stays in central pane and reopens from settings', async ({ page }) => {
  await page.goto('/');
  const wizard = page.locator('.app-layout__tab-content > .provider-wizard');
  await expect(wizard).toBeVisible();
  await expect(page.locator('#compose-input')).toBeHidden();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await wizard.getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(page.locator('#compose-input')).toBeVisible();
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.locator('#panel-settings').getByRole('button', { name: 'Provider setup', exact: true }).click();
  await expect(wizard).toBeVisible();
  await expect(page.locator('#panel-settings')).toBeHidden();
  await wizard.getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(page.locator('#compose-input')).toBeVisible();
});
