import { expect, test } from '@playwright/test';
import {installLiveStream} from '../fixtures/live-stream.mjs';

test('session navigation renders Tau sessions through Piclaw sidebar cards', async ({ page }) => {
  await installLiveStream(page,'tau');
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeAttached();
  await expect.poll(async () => (await page.locator('#app-status').textContent())?.trim() ?? '').not.toMatch(/Loading Tau shell/i);
  const cancelOnboarding = page.getByRole('button', { name: 'Cancel' });
  await cancelOnboarding.waitFor({ state: 'visible', timeout: 2000 }).catch(() => {});
  if (await cancelOnboarding.isVisible()) await cancelOnboarding.click();
  await page.evaluate(() => {
    window.__tauSelectedSession = null;
    window.addEventListener('tau:session-select', (event) => { window.__tauSelectedSession = event.detail.sessionId; }, { once: true });
    window.dispatchEvent(new CustomEvent('tau:sessions-render', { detail: { items: [
      { sessionId: 'session-1', title: 'Primary session', meta: 'anthropic/claude · active', active: true },
      { sessionId: 'session-2', title: 'Review session', meta: 'openai/gpt', active: false },
    ] } }));
  });

  await page.getByRole('button', { name: 'Open sessions', exact: true }).first().click();
  const list = page.locator('#session-list');
  await expect(list.locator('.sessions-panel__session')).toHaveCount(2);
  await expect(page.locator('#session-count')).toHaveText('2 sessions');
  await expect(list.locator('.sessions-panel__session').first()).toHaveAttribute('data-active', 'true');
  await list.getByRole('button', { name: /Review session/ }).click();
  await expect.poll(() => page.evaluate(() => window.__tauSelectedSession)).toBe('session-2');
});
