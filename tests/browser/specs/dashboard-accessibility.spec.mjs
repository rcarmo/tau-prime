import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
for(const colorScheme of ['light','dark']) {
 test(`${colorScheme} populated Dashboard is accessible and within viewport`,async({page})=>{
  await page.emulateMedia({colorScheme});
  await page.route('**/dashboard*',r=>r.fulfill({contentType:'application/json',body:JSON.stringify({sessions:[{session_id:'review',title:'Build review',agent_name:'review',workspace:'/workspace',model:'test/model',preview:'Ready for review',preview_kind:'summary',queue_count:2,context_used_tokens:500,context_window_tokens:1000,context_percent:50,activity_state:'idle'}],page:1,total_pages:2,total:2,generated_at:'2026-09-01T12:00:00Z'})}));
  await page.goto('/',{waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancel=page.getByRole('button',{name:'Cancel',exact:true});
  await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});
  if(await cancel.isVisible()) await cancel.click();
  await expect(page.locator('#compose-input')).toBeVisible();
  await page.getByRole('button',{name:'Dashboard',exact:true}).click();
  const dialog=page.getByRole('dialog',{name:'Session dashboard'});
  await expect(dialog.locator('.dashboard-tile')).toHaveCount(1);
  const result=await new AxeBuilder({page}).include('#session-dashboard').analyze();
  expect(result.violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))).toEqual([]);
  const overflow=await dialog.evaluate(el=>{const r=el.getBoundingClientRect();return {left:r.left,right:r.right,viewport:innerWidth,overflow:el.scrollWidth-el.clientWidth};});
  expect(overflow.left).toBeGreaterThanOrEqual(0);expect(overflow.right).toBeLessThanOrEqual(overflow.viewport);expect(overflow.overflow).toBeLessThanOrEqual(1);
 });
}
