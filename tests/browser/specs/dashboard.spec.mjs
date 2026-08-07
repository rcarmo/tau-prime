import { expect, test } from '@playwright/test';

test('dashboard renders Tau sessions as Piclaw-managed tiles', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeVisible();
  await expect.poll(async () => (await page.locator('#app-status').textContent())?.trim() ?? '').not.toMatch(/Loading Tau shell/i);
  const cancel = page.getByRole('button', { name: 'Cancel' });
  await cancel.waitFor({ state: 'visible', timeout: 2000 }).catch(() => {});
  if (await cancel.isVisible()) await cancel.click();
  await page.evaluate(() => window.dispatchEvent(new CustomEvent('tau:dashboard-render', { detail: {
    sessions: [{ session_id: 'session-1', title: 'Build review', agent_name: 'review', workspace: '/workspace', model: 'claude', preview_kind: 'summary', preview: 'Ready', queue_count: 2, context_used_tokens: 500, context_window_tokens: 1000, context_percent: 50, activity_state: 'running', last_activity: new Date().toISOString() }],
    page: 1, totalPages: 2, generatedAt: new Date().toISOString(), loading: false, selectedSessionId: 'session-1',
  } })));
  await page.locator('#session-dashboard').evaluate((element) => { element.hidden = false; });
  const tile = page.locator('#dashboard-grid .dashboard-tile');
  await expect(tile).toHaveCount(1);
  await expect(tile).toHaveAttribute('data-selected', 'true');
  await expect(tile.locator('.dashboard-agent')).toHaveText('Build review');
  await expect(tile.locator('.dashboard-context-fill')).toHaveAttribute('style', /50%/);
  await expect(page.locator('#dashboard-next')).toBeEnabled();
});
