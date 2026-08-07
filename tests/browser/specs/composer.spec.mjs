import { expect, test } from '@playwright/test';

test('composer renders staged attachments through Piclaw chip markup', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeVisible();
  await expect.poll(async () => (await page.locator('#app-status').textContent())?.trim() ?? '').not.toMatch(/Loading Tau shell/i);
  const cancelOnboarding = page.getByRole('button', { name: 'Cancel' });
  await cancelOnboarding.waitFor({ state: 'visible', timeout: 2000 }).catch(() => {});
  if (await cancelOnboarding.isVisible()) await cancelOnboarding.click();
  await page.evaluate(() => {
    window.__tauRemovedAttachment = null;
    window.addEventListener('tau:attachment-remove', (event) => { window.__tauRemovedAttachment = event.detail.mediaId; }, { once: true });
    window.dispatchEvent(new CustomEvent('tau:attachments-render', { detail: { busy: false, items: [
      { mediaId: 'media-7', filename: 'notes.txt', label: 'notes.txt · 2 KB' },
    ] } }));
  });

  const chip = page.locator('#compose-attachment-list .chat__attachment-pill');
  await expect(chip).toHaveCount(1);
  await expect(chip.locator('.chat__attachment-name')).toHaveText('notes.txt · 2 KB');
  await expect(page.locator('#compose-clear-attachments')).toBeVisible();
  await chip.getByRole('button', { name: 'Remove attachment notes.txt' }).evaluate((button) => button.click());
  await expect.poll(() => page.evaluate(() => window.__tauRemovedAttachment)).toBe('media-7');
});
