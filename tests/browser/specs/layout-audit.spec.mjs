import { expect, test } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

test('capture current shell and workspace for visual audit', async ({ page }, info) => {
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeAttached();
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancel = page.getByRole('button', { name: 'Cancel', exact: true });
  await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});
  if (await cancel.isVisible()) await cancel.click();
  await page.evaluate(() => document.fonts.ready);
  const dir = '/workspace/tmp/tau-classic-audit';
  await mkdir(dir, { recursive: true });
  await page.screenshot({ path: path.join(dir, `${info.project.name}-shell.png`) });
  await page.getByRole('button', { name: 'Open sessions', exact: true }).click();
  await page.getByRole('group', { name: 'Navigation', exact: true }).getByRole('button', { name: 'Workspace', exact: true }).click();
  await expect(page.locator('#side-panel')).toBeVisible();
  await page.screenshot({ path: path.join(dir, `${info.project.name}-workspace.png`) });
});
