import { expect, test } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

test('capture current shell and workspace for visual audit', async ({ page }, info) => {
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeAttached();
  await expect.poll(async () => (await page.locator('#app-status').textContent())?.trim() ?? '').not.toMatch(/Loading Tau shell/i);
  const cancel = page.getByRole('button', { name: 'Cancel', exact: true });
  if (await cancel.isVisible()) await cancel.click();
  await page.evaluate(() => document.fonts.ready);
  const dir = '/workspace/tmp/tau-audit-september';
  await mkdir(dir, { recursive: true });
  await page.screenshot({ path: path.join(dir, `${info.project.name}-shell.png`) });
  await page.getByRole('button', { name: 'Workspace', exact: true }).first().click();
  await expect(page.locator('#side-panel')).toBeVisible();
  await page.screenshot({ path: path.join(dir, `${info.project.name}-workspace.png`) });
});
