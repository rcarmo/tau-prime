import { expect, test } from '@playwright/test';

async function showApproval(page, id) {
  await page.evaluate((approvalId) => window.dispatchEvent(new CustomEvent('tau:approval-render', { detail: { approval: {
    approval_id: approvalId,
    status: 'pending',
    tool_name: 'bash',
    description: 'Run a workspace command',
    arguments: { command: 'git status' },
  } } })), id);
}

test('approval dialog uses Piclaw modal mapping and Escape denies safely', async ({ page }) => {
  await page.addInitScript(() => {
    const nativeFetch = window.fetch.bind(window);
    window.fetch = (input, init) => {
      const url = typeof input === 'string' ? input : input.url;
      if (url.includes('/api/approvals/')) return Promise.resolve(new Response(JSON.stringify({ status: 'resolved' }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
      return nativeFetch(input, init);
    };
  });
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeVisible();
  await expect.poll(async () => (await page.locator('#app-status').textContent())?.trim() ?? '').not.toMatch(/Loading Tau shell/i);
  const cancelOnboarding = page.getByRole('button', { name: 'Cancel' });
  await cancelOnboarding.waitFor({ state: 'visible', timeout: 2000 }).catch(() => {});
  if (await cancelOnboarding.isVisible()) await cancelOnboarding.click();
  await page.evaluate(() => {
    window.__tauApprovalResponses = [];
    window.addEventListener('tau:approval-response', (event) => window.__tauApprovalResponses.push(event.detail));
  });

  await showApproval(page, 'approval-deny');
  const dialog = page.getByRole('alertdialog');
  await expect(dialog).toBeVisible();
  await expect(dialog).toContainText('Allow bash?');
  await expect(dialog).toContainText('git status');
  await expect(page.getByRole('button', { name: 'Deny' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect.poll(() => page.evaluate(() => window.__tauApprovalResponses)).toEqual([{ approvalId: 'approval-deny', decision: 'deny' }]);
  await expect(dialog).toBeHidden();

  await page.evaluate(() => window.dispatchEvent(new CustomEvent('tau:approval-render', { detail: { approval: null } })));
  await showApproval(page, 'approval-allow');
  await page.getByRole('button', { name: 'Allow once' }).click();
  await expect.poll(() => page.evaluate(() => window.__tauApprovalResponses.at(-1))).toEqual({ approvalId: 'approval-allow', decision: 'allow' });
});
