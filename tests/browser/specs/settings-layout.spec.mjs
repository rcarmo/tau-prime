import { expect, test } from '@playwright/test';

test('settings in classic dialog without remounting Tau API form anchors', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#compose-input')).toBeAttached();
  await expect.poll(async () => (await page.locator('#app-status').textContent())?.trim() ?? '').not.toMatch(/Loading Tau shell/i);
  const cancel = page.getByRole('button', { name: 'Cancel', exact: true });
  await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});
  if(await cancel.isVisible())await cancel.click();
  await page.getByRole('button',{name:'Open sessions',exact:true}).click();
  await page.evaluate(() => { window.__authAnchor = document.getElementById('auth-form'); });
  const settings = page.getByRole('button', { name: 'Settings', exact: true });
  await settings.click();
  await expect(page.locator('.settings-dialog > #panel-settings')).toBeVisible();
  await expect(page.locator('#auth-token')).toBeVisible();
  const overflow = await page.locator('#panel-settings').evaluate(el => ({
    scroll: el.scrollWidth - el.clientWidth,
    controls: [...el.querySelectorAll('input, select, button')].filter(control => {
      const r=control.getBoundingClientRect(), p=el.getBoundingClientRect();
      return r.width>0 && (r.left<p.left-1 || r.right>p.right+1);
    }).map(control=>control.id || control.className),
  }));
  expect(overflow.scroll).toBeLessThanOrEqual(1);
  expect(overflow.controls).toEqual([]);
  const modelCategory=page.getByRole('link',{name:'Model',exact:true});
  await modelCategory.focus(); await page.keyboard.press('Enter');
  await expect(modelCategory).toHaveAttribute('aria-current','location');
  await expect(page.locator('.settings-nav-item.active')).toHaveCount(1);
  await expect(page.getByRole('link',{name:'Authentication',exact:true})).not.toHaveAttribute('aria-current','location');
  await page.getByRole('button',{name:'Close settings',exact:true}).click();
  await expect(page.locator('#panel-settings')).toBeHidden();
  await expect(page.locator('#compose-input')).toBeVisible();
  expect(await page.evaluate(() => window.__authAnchor === document.getElementById('auth-form'))).toBe(true);
});
