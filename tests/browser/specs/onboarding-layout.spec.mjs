import { expect, test } from '@playwright/test';

test('provider setup stays in central pane and reopens from settings', async ({ page }) => {
  await page.goto('/');
  const wizard = page.locator('.container > .provider-wizard');
  await expect(wizard).toBeVisible();
  await expect(page.locator('#compose-input')).toBeHidden();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await wizard.getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(page.locator('#compose-input')).toBeVisible();
  await page.locator('#compose-input').fill('Draft survives setup');
  await page.getByRole('button', { name: 'Open sessions', exact: true }).click();
  await page.getByRole('group', { name: 'Navigation', exact: true }).getByRole('button', { name: 'Settings', exact: true }).click();
  await page.locator('#panel-settings').getByRole('button', { name: 'Provider setup', exact: true }).click();
  await expect(wizard).toBeVisible();
  await expect(page.locator('#panel-settings')).toBeHidden();
  await expect(page.locator('#compose-input')).toHaveValue('Draft survives setup');
  await wizard.getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(page.locator('#compose-input')).toBeVisible();
});
