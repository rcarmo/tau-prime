import { expect, test } from '@playwright/test';

test('dashboard moves focus inside, traps Tab, and restores focus on Escape', async ({page})=>{
  await page.goto('/',{waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancel=page.getByRole('button',{name:'Cancel',exact:true});
  await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});
  if(await cancel.isVisible()) await cancel.click();
  const trigger=page.getByRole('button',{name:'Dashboard',exact:true});
  await trigger.focus(); await page.keyboard.press('Enter');
  const dialog=page.getByRole('dialog',{name:'Session dashboard'});
  await expect(dialog).toBeVisible();
  await expect(page.locator('#dashboard-close')).toBeFocused();
  expect(await page.locator('#compose-input').evaluate(el => Boolean(el.closest('[inert]')))).toBe(true);
  await page.locator('#compose-input').evaluate(el => el.focus());
  await expect(page.locator('#dashboard-close')).toBeFocused();
  await page.keyboard.press('Shift+Tab');
  await expect(page.locator('#dashboard-manage')).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(page.locator('#dashboard-close')).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
  await expect(trigger).toBeFocused();
  expect(await page.locator('#compose-input').evaluate(el => Boolean(el.closest('[inert]')))).toBe(false);
  await page.locator('#compose-input').focus();
  await expect(page.locator('#compose-input')).toBeFocused();
});
