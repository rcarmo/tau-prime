import {test,expect} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
import {installSelectedSession} from '../fixtures/selected-session.mjs';
import {installLiveStream} from '../fixtures/live-stream.mjs';

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

for(const colorScheme of ['light','dark']) test(`classic populated ${colorScheme} preview fits viewport`,async({page},info)=>{
 await installSelectedSession(page);await installLiveStream(page,'tau');await page.emulateMedia({colorScheme});
 await page.goto('/?ui=classic',{waitUntil:'domcontentloaded'});
 await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});if(await cancel.isVisible())await cancel.click();
 await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tau:timeline-render',{detail:{selected:true,items:[{id:'one',role:'user',content:'Review the workspace and preserve the existing API.',meta:'2m'},{id:'two',role:'assistant',content:'## Workspace review\n\nThe API is **unchanged**.\n\n- Routes retained\n- Streaming retained',meta:'1m'}]}})));
 await expect(page.locator('#post-two strong')).toHaveText('unchanged');
 await page.evaluate(()=>document.fonts.ready);
 const input=await page.locator('#compose-input').boundingBox();const vp=page.viewportSize();
 expect(input.x).toBeGreaterThanOrEqual(0);expect(input.x+input.width).toBeLessThanOrEqual(vp.width+1);
 expect(input.y+input.height).toBeLessThanOrEqual(vp.height+1);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(vp.width);
 await mkdir('/workspace/tmp/tau-classic-preview',{recursive:true});
 await page.screenshot({path:`/workspace/tmp/tau-classic-preview/${info.project.name}-${colorScheme}.png`});
});

for(const via of ['button','keyboard']) test(`classic ${via} submission preserves API payload and draft on failure`,async({page})=>{
 await installSelectedSession(page);await installLiveStream(page,'tau');
 const submitted=[];let fail=true;
 await page.route('**/api/sessions/visual-review/runs',route=>{
  if(route.request().method()!=='POST')return route.fallback();
  submitted.push(route.request().postDataJSON());
  return route.fulfill({status:fail?500:201,json:fail?{error:'Fixture rejection'}:{run_id:'classic-run',status:'pending'}});
 });
 await page.goto('/?ui=classic',{waitUntil:'domcontentloaded'});
 await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});if(await cancel.isVisible())await cancel.click();
 const input=page.locator('#compose-input');await input.fill('Review');
 await input.press('Shift+Enter');await input.press('End');await input.type('the workspace');
 await expect(input).toHaveValue('Review\nthe workspace');expect(submitted).toHaveLength(0);
 const send=()=>via==='button'?page.locator('#compose-submit').click():input.press('Enter');
 await send();await expect.poll(()=>submitted.length).toBe(1);
 await expect(page.locator('#compose-submit')).toBeEnabled();
 await expect(input).toHaveValue('Review\nthe workspace');
 fail=false;await send();await expect.poll(()=>submitted.length).toBe(2);
 await expect(input).toHaveValue('');
 expect(submitted).toEqual([{content:'Review\nthe workspace'},{content:'Review\nthe workspace'}]);
 await expect(page.locator('#compose-delivery-mode')).toBeHidden();
});
