import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
for(const colorScheme of ['light','dark']) {
 test(`${colorScheme} workspace and plan controls stay accessible`,async({page})=>{
  await page.emulateMedia({colorScheme});
  await page.route('**/api/events*',r=>r.fulfill({contentType:'text/event-stream',body:': fixture\n\n'}));
  await page.goto('/',{waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancel=page.getByRole('button',{name:'Cancel',exact:true});
  await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});
  if(await cancel.isVisible())await cancel.click();
  await page.getByRole('button',{name:'Open sessions',exact:true}).click();
  for(const name of ['Workspace','Plan']) {
   await page.getByRole('button',{name,exact:true}).first().click();
   const selector=name==='Workspace'?'#panel-workspace':'#panel-plan';
   await expect(page.locator(selector)).toBeVisible();
   if(name==='Plan') {
    await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tau:plan-render',{detail:{draft:'- [ ] Review workspace',revision:2,dirty:true,disabled:false,reloadDisabled:false,conflict:false,status:'Draft has unsaved changes.'}})));
    await expect(page.locator('#plan-reload-button')).toBeEnabled();
    await expect(page.locator('#plan-save-button')).toBeEnabled();
   }
   await page.evaluate(async()=>{await Promise.all(document.getAnimations().filter(a=>Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{})));});
   const result=await new AxeBuilder({page}).include(selector).analyze();
   expect(result.violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))).toEqual([]);
   const outside=await page.locator(selector).evaluate(el=>{const p=el.getBoundingClientRect();return [...el.querySelectorAll('button,input,textarea,select')].filter(c=>{const r=c.getBoundingClientRect();return r.width>0&&(r.left<p.left-1||r.right>p.right+1);}).map(c=>c.id||c.className);});
   expect(outside).toEqual([]);
  }
 });
}
