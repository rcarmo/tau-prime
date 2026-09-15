import {test,expect} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
import {installSelectedSession} from '../fixtures/selected-session.mjs';
import {installLiveStream} from '../fixtures/live-stream.mjs';

test('classic shell boots the real Tau adapter with session navigation',async({page})=>{
 await installSelectedSession(page);await installLiveStream(page,'tau');
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/',{waitUntil:'domcontentloaded'});
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
 await page.goto('/',{waitUntil:'domcontentloaded'});
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
 await page.goto('/',{waitUntil:'domcontentloaded'});
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

 test('classic secondary panels keep controls within the viewport',async({page})=>{
 await installSelectedSession(page);await installLiveStream(page,'tau');
 await page.goto('/',{waitUntil:'domcontentloaded'});
 await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});if(await cancel.isVisible())await cancel.click();
 await page.getByRole('button',{name:'Open sessions',exact:true}).click();
 for(const name of ['Workspace','Search','Plan','Settings']) {
  await page.getByRole('group',{name:'Navigation',exact:true}).getByRole('button',{name,exact:true}).click();
  const panel=page.locator(`#panel-${name.toLowerCase()}`);await expect(panel).toBeVisible();
  const outside=await panel.locator('input,textarea,select,button').evaluateAll(els=>els.filter(el=>{
   const r=el.getBoundingClientRect();return r.width>0&&r.height>0&&(r.left < -1||r.right>innerWidth+1);
  }).map(el=>el.id||el.textContent));
  expect(outside).toEqual([]);
 }
 const last=page.locator('#panel-settings button:visible').last();
 await last.scrollIntoViewIfNeeded();
 const box=await last.boundingBox();
 expect(box.y).toBeGreaterThanOrEqual(0);
 expect(box.y+box.height).toBeLessThanOrEqual(page.viewportSize().height+1);
 await page.getByRole('button',{name:'Close settings',exact:true}).click();
 await expect(page.locator('.app-shell')).toHaveClass(/workspace-collapsed/);
 await expect(page.locator('#compose-input')).toBeVisible();
 });

test('classic composer resize supports keyboard and pointer without changing draft',async({page})=>{
 await installSelectedSession(page);await installLiveStream(page,'tau');await page.goto('/');
 await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});if(await cancel.isVisible())await cancel.click();
 const input=page.locator('#compose-input'),handle=page.getByRole('separator',{name:'Resize message input'});
 const baseline=(await input.boundingBox()).height;
 await input.fill('Keep this draft');await handle.focus();await page.keyboard.press('ArrowUp');
 await expect(input).toHaveCSS('height',`${baseline+10}px`);await page.keyboard.press('Home');await expect(input).toHaveCSS('height',`${baseline}px`);
 const box=await handle.boundingBox();await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();await page.mouse.move(box.x+box.width/2,box.y+box.height/2-40);await page.mouse.up();
 await expect(input).toHaveCSS('height',`${baseline+40}px`);await expect(input).toHaveValue('Keep this draft');
 await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tau:completion-render',{detail:{open:false,index:0,items:[]}})));
 await expect(input).toHaveCSS('height',`${baseline+40}px`);
 await handle.focus();for(let i=0;i<60;i++)await page.keyboard.press('ArrowUp');
 const max=Number(await handle.getAttribute('aria-valuemax'));
 expect(Math.abs((await input.boundingBox()).height-max)).toBeLessThanOrEqual(1);
 expect(Number(await handle.getAttribute('aria-valuenow'))).toBeLessThanOrEqual(max+1);
 await page.keyboard.press('Home');await expect(input).toHaveCSS('height',`${baseline}px`);
 await expect(handle).toHaveAttribute('aria-valuemin',String(baseline));
});

test('composer clamps resize state when viewport changes',async({page})=>{
 await installSelectedSession(page);await installLiveStream(page,'tau');await page.setViewportSize({width:1440,height:900});await page.goto('/');
 await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});if(await cancel.isVisible())await cancel.click();
 const input=page.locator('#compose-input'),handle=page.getByRole('separator',{name:'Resize message input'});
 await input.fill('Preserve on rotation');await handle.focus();for(let i=0;i<40;i++)await page.keyboard.press('ArrowUp');
 await page.setViewportSize({width:390,height:600});
 await expect(handle).toHaveAttribute('aria-valuemax','180');
 await expect(handle).toHaveAttribute('aria-valuemin','50');
 await expect(input).toHaveCSS('height','180px');
 await expect(input).toHaveValue('Preserve on rotation');
 await page.setViewportSize({width:1440,height:900});
 await expect(handle).toHaveAttribute('aria-valuemin','70');
 await expect(handle).toHaveAttribute('aria-valuemax','450');
 await handle.focus();await page.keyboard.press('Home');await expect(input).toHaveCSS('height','70px');
});

test('classic workspace edge toggle opens navigation and closes it',async({page})=>{
 await installSelectedSession(page);await installLiveStream(page,'tau');await page.goto('/');
 await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const toggle=page.locator('.workspace-toggle-tab');
 // Upstream hides the edge control at some widths; semantics remain wired.
 if(await toggle.isVisible()) {
  await toggle.click();await expect(page.locator('#panel-workspace')).toBeVisible();
  await expect(toggle).toHaveAttribute('aria-expanded','true');
  await toggle.click();await expect(page.locator('.app-shell')).toHaveClass(/workspace-collapsed/);
 }
});

test('classic model hint opens existing model settings with keyboard focus',async({page})=>{
 await installSelectedSession(page);await installLiveStream(page,'tau');await page.goto('/');
 await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});if(await cancel.isVisible())await cancel.click();
 await page.getByRole('button',{name:'Open model settings',exact:true}).focus();await page.keyboard.press('Enter');
 await expect(page.locator('#panel-settings')).toBeVisible();
 await expect(page.locator('#model-input')).toBeFocused();
 await expect(page.getByRole('link',{name:'Model',exact:true})).toHaveAttribute('aria-current','location');
 await expect(page.getByRole('link',{name:'Authentication',exact:true})).not.toHaveAttribute('aria-current','location');
 await expect(page.locator('#model-form')).toHaveCount(1);
});
