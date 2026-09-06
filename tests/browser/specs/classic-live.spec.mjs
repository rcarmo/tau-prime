import {test,expect} from '@playwright/test';

test('classic preview boots the real Tau adapter with session navigation',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/?ui=classic',{waitUntil:'domcontentloaded'});
 await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});if(await cancel.isVisible())await cancel.click();
 await expect(page.locator('#compose-input')).toBeVisible();
 await expect(page.locator('.app-layout,.activity-bar')).toHaveCount(0);
 await expect(page.locator('#compose-delivery-mode')).toBeHidden();
 await page.getByRole('button',{name:'Open sessions',exact:true}).click();
 await expect(page.locator('#panel-sessions')).toBeVisible();
 expect(errors).toEqual([]);
});
