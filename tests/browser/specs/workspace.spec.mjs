import { expect, test } from '@playwright/test';

test('workspace tree and annotations render through Preact', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeVisible();
  await expect.poll(async () => (await page.locator('#app-status').textContent())?.trim() ?? '').not.toMatch(/Loading Tau shell/i);
  const cancel = page.getByRole('button', { name: 'Cancel' });
  await cancel.waitFor({ state: 'visible', timeout: 2000 }).catch(() => {});
  if (await cancel.isVisible()) await cancel.click();
  await page.evaluate(() => window.dispatchEvent(new CustomEvent('tau:workspace-render', { detail: {
    path: '/workspace/src', filePath: 'app.ts', content: 'const value = 1;',
    entries: [{ name: 'components', kind: 'directory', path: '/workspace/src/components' }, { name: 'app.ts', kind: 'file', path: '/workspace/src/app.ts' }],
    annotations: [{ line: 1, endLine: null, severity: 'warning', source: 'lint', message: 'Review value' }],
  } })));
  await page.getByRole('button', { name: 'Workspace', exact: true }).first().click();
  await expect(page.locator('#workspace-path')).toHaveText('/workspace/src');
  await expect(page.locator('#workspace-list .file-tree__item')).toHaveCount(2);
  await expect(page.locator('#workspace-editor')).toHaveValue('const value = 1;');
  await expect(page.locator('#workspace-annotation-list')).toContainText('Line 1 · lint: Review value');
});
