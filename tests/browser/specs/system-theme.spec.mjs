import { expect, test } from '@playwright/test';

test('classic shell follows system theme without visual-mode tokens', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('/');
  await expect(page.locator('html')).toHaveAttribute('data-tau-ui','classic');
  const background=()=>page.locator('html').evaluate(el=>getComputedStyle(el).getPropertyValue('--bg-primary').trim());
  await expect.poll(background).toBe('#fff');
  await page.emulateMedia({ colorScheme: 'dark' });
  await expect.poll(background).toBe('#000');
  await expect(page.locator('link[href*="piclaw-reference"],link[href*="piclaw-parity"]')).toHaveCount(0);
});
