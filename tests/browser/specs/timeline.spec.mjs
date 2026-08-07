import { expect, test } from '@playwright/test';

test('timeline uses Piclaw message, tool, and attachment component mapping', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeVisible();
  await expect.poll(async () => (await page.locator('#app-status').textContent())?.trim() ?? '').not.toMatch(/Loading Tau shell/i);
  const cancelOnboarding = page.getByRole('button', { name: 'Cancel' });
  await cancelOnboarding.waitFor({ state: 'visible', timeout: 2000 }).catch(() => {});
  if (await cancelOnboarding.isVisible()) await cancelOnboarding.click();

  await page.evaluate(() => window.dispatchEvent(new CustomEvent('tau:timeline-render', { detail: {
    selected: true,
    items: [
      { id: 'user-1', role: 'user', content: 'Inspect this file', meta: 'Entry user', attachments: [{ mediaId: 'media-1', filename: 'notes.txt', mediaType: 'text/plain' }] },
      { id: 'assistant-1', role: 'assistant', content: 'I will inspect it.', meta: 'Entry assistant', toolCalls: [{ id: 'call-1', name: 'read', arguments: { path: 'notes.txt' } }] },
      { id: 'tool-1', role: 'tool', content: 'file contents', meta: 'Entry tool', toolCallId: 'call-1', toolName: 'read', toolOk: true },
    ],
  } })));

  const timeline = page.locator('#timeline-list');
  await expect(timeline.locator('.message-list__item')).toHaveCount(2);
  await expect(timeline.locator('.attachment-chip__name')).toHaveText('notes.txt');
  const tool = timeline.locator('.message-list__tool-call');
  await expect(tool.locator('.message-list__tool-call-badge')).toHaveText('done');
  await tool.locator('.message-list__tool-call-header').click();
  await expect(tool.locator('.message-list__tool-call-code')).toHaveCount(2);
  await expect(tool).toContainText('file contents');
});
