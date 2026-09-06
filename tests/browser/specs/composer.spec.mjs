import { expect, test } from '@playwright/test';

test('composer renders staged attachments through Piclaw chip markup', async ({ page }) => {
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#compose-input')).toBeAttached();
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready', 'true');
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

  const chip = page.locator('#compose-attachment-list .compose-file-pill');
  await expect(chip).toHaveCount(1);
  await expect(chip.locator('.compose-file-name')).toHaveText('notes.txt · 2 KB');
  await expect(page.locator('#compose-clear-attachments')).toBeVisible();
  await chip.getByRole('button', { name: 'Remove attachment notes.txt' }).evaluate((button) => button.click());
  await expect.poll(() => page.evaluate(() => window.__tauRemovedAttachment)).toBe('media-7');
});

test('composer exposes Send without a visible Run delivery selector', async ({ page }) => {
  await page.goto('/', {waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready', 'true');
  const cancel = page.getByRole('button', {name:'Cancel',exact:true});
  if (await cancel.isVisible()) await cancel.click();
  await expect(page.locator('#compose-delivery-mode')).toBeHidden();
  await expect(page.getByRole('combobox', {name:'Message delivery'})).toHaveCount(0);
  await expect(page.locator('#compose-submit')).toHaveAccessibleName('Send');
  await expect(page.locator('#compose-delivery-mode')).toHaveValue('run');
});
