import { expect, test } from '@playwright/test';

test('shell applies Piclaw system theme classes and tokens and follows changes', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('/');
  await expect(page.locator('html')).toHaveClass(/light/);
  expect(await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--bg').trim())).toBe('#f3f3f3');
  await page.emulateMedia({ colorScheme: 'dark' });
  await expect(page.locator('html')).toHaveClass(/dark/);
  expect(await page.locator('html').evaluate(el => getComputedStyle(el).getPropertyValue('--bg').trim())).toBe('#1e1e2e');
});
