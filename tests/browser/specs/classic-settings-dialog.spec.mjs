import {test,expect} from '@playwright/test';
import {installSelectedSession} from '../fixtures/selected-session.mjs';
import {installLiveStream} from '../fixtures/live-stream.mjs';
test('classic Settings is modal and keeps form state on close',async({page})=>{
 await installSelectedSession(page);await installLiveStream(page,'tau');await page.goto('/');await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});if(await cancel.isVisible())await cancel.click();
 await page.evaluate(()=>window.savedAuthForm=document.getElementById('auth-form'));
 const trigger=page.getByRole('button',{name:'Open model settings',exact:true});await trigger.click();
 await expect(page.getByRole('dialog',{name:'Settings',exact:true})).toBeVisible();
 await expect(page.locator('#model-input')).toBeFocused();
 expect(await page.locator('#compose-input').evaluate(el=>!!el.closest('[inert]'))).toBe(true);
 await page.locator('#model-input').fill('unsaved-model');await page.keyboard.press('Escape');
 await expect(page.getByRole('dialog',{name:'Settings',exact:true})).toBeHidden();await expect(trigger).toBeFocused();
 await trigger.click();await expect(page.locator('#model-input')).toHaveValue('unsaved-model');
 expect(await page.evaluate(()=>window.savedAuthForm===document.getElementById('auth-form'))).toBe(true);
});
