import { expect, test } from '@playwright/test';

const queued = [
  { queue_id: 'follow-1', session_id: 'queue-test', queue_kind: 'follow_up', position: 0, content: 'First follow-up', consumed_at: null },
  { queue_id: 'follow-2', session_id: 'queue-test', queue_kind: 'follow_up', position: 1, content: 'Second follow-up', consumed_at: null },
  { queue_id: 'steer-1', session_id: 'queue-test', queue_kind: 'steer', position: 0, content: 'Urgent steer', consumed_at: null },
];

test('queue stack preserves independent FIFO heads and uses Tau dispatch routes', async ({ page }) => {
  await page.addInitScript((items) => {
    const nativeFetch = window.fetch.bind(window);
    window.__tauDispatched = [];
    window.fetch = async (input, init) => {
      const url = typeof input === 'string' ? input : input.url;
      if (url.endsWith('/api/sessions/queue-test/queue')) {
        return new Response(JSON.stringify({ queue: items }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.endsWith('/api/sessions/queue-test/runs')) {
        return new Response(JSON.stringify({ runs: [{ run_id: 'run-active', session_id: 'queue-test', status: 'running' }] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.includes('/api/runs/run-active/queue/') && url.endsWith('/dispatch')) {
        window.__tauDispatched.push(url);
        return new Response(JSON.stringify({ ...items[0], consumed_at: '2026-08-07T00:00:00Z' }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      return nativeFetch(input, init);
    };
  }, queued);

  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeVisible();
  await expect.poll(async () => (await page.locator('#app-status').textContent())?.trim() ?? '').not.toMatch(/Loading Tau shell/i);
  const cancelOnboarding = page.getByRole('button', { name: 'Cancel' });
  await cancelOnboarding.waitFor({ state: 'visible', timeout: 2000 }).catch(() => {});
  if (await cancelOnboarding.isVisible()) await cancelOnboarding.click();
  await page.evaluate(() => window.dispatchEvent(new CustomEvent('tau:session-selected', { detail: { sessionId: 'queue-test' } })));

  const stack = page.locator('.queue-stack');
  await expect(stack.locator('.queue-stack__item')).toHaveCount(3);
  await expect(stack.getByRole('button', { name: /Dispatch/ })).toHaveCount(2);
  await expect(stack.getByText('First follow-up')).toBeVisible();
  await expect(stack.getByText('Second follow-up')).toBeVisible();

  await stack.locator('.queue-stack__item').filter({ hasText: 'First follow-up' }).getByRole('button', { name: /Dispatch/ }).click();
  const dispatched = await page.evaluate(() => window.__tauDispatched);
  expect(dispatched).toHaveLength(1);
  expect(dispatched[0]).toContain('/api/runs/run-active/queue/follow_up/dispatch');

  await stack.locator('.queue-stack__item').filter({ hasText: 'Urgent steer' }).getByRole('button', { name: 'Copy queued message to compose' }).click();
  await expect(page.locator('#compose-input')).toHaveValue('Urgent steer');
});
