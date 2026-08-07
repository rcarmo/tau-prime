import { expect, test } from '@playwright/test';

test('plan panel renders Tau revision and conflict state through Piclaw task markup', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeVisible();
  await expect.poll(async () => (await page.locator('#app-status').textContent())?.trim() ?? '').not.toMatch(/Loading Tau shell/i);
  const cancelOnboarding = page.getByRole('button', { name: 'Cancel' });
  await cancelOnboarding.waitFor({ state: 'visible', timeout: 2000 }).catch(() => {});
  if (await cancelOnboarding.isVisible()) await cancelOnboarding.click();

  await page.getByRole('button', { name: 'Plan', exact: true }).first().click();
  await page.evaluate(() => window.dispatchEvent(new CustomEvent('tau:plan-render', { detail: {
    draft: '- [ ] Review queue behavior', revision: 7, dirty: true, disabled: false,
    reloadDisabled: false, conflict: true, status: 'Server revision 8 is newer than your draft.',
  } })));

  const panel = page.locator('#panel-plan');
  await expect(panel).toBeVisible();
  await expect(panel.locator('#plan-revision')).toHaveText('Revision 7');
  await expect(panel.locator('#plan-editor')).toHaveValue('- [ ] Review queue behavior');
  await expect(panel.locator('#plan-status')).toHaveText('Server revision 8 is newer than your draft.');
  await expect(panel.locator('#plan-conflict')).toBeVisible();
  await expect(panel.locator('#plan-save-button')).toBeEnabled();
  await expect(panel.locator('#plan-reload-button')).toBeEnabled();
});
