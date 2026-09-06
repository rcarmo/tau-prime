import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
for(const colorScheme of ['light','dark']) {
 test(`${colorScheme} populated search is accessible and within pane`,async({page})=>{
  await page.emulateMedia({colorScheme});
  await page.route('**/api/events*',r=>r.fulfill({contentType:'text/event-stream',body:': fixture\n\n'}));
  await page.goto('/',{waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancel=page.getByRole('button',{name:'Cancel',exact:true});
  await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});
  if(await cancel.isVisible()) await cancel.click();
  await page.getByRole('button',{name:'Open sessions',exact:true}).click();
  await page.getByRole('group',{name:'Navigation',exact:true}).getByRole('button',{name:'Search',exact:true}).click();
  await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tau:search-render',{detail:{items:[{entityType:'message',entityId:'review-result',meta:'Review session · Rank 1.25',text:'Matching workspace content with a long descriptive result.',sessionId:'review'}]}})));
  await expect(page.locator('.tau-search-result')).toHaveCount(1);
  const result=await new AxeBuilder({page}).include('#panel-search').analyze();
  expect(result.violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))).toEqual([]);
  const outside=await page.locator('#panel-search').evaluate(el=>{const p=el.getBoundingClientRect();return [...el.querySelectorAll('input,button')].filter(c=>{const r=c.getBoundingClientRect();return r.width>0&&(r.left<p.left-1||r.right>p.right+1);}).map(c=>c.id||c.textContent);});
  expect(outside).toEqual([]);
 });
}
