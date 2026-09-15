import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

for(const colorScheme of ['light','dark']) {
  test(`${colorScheme} onboarding has no serious accessibility violations`, async ({page})=>{
    await page.emulateMedia({colorScheme});
    await page.goto('/',{waitUntil:'domcontentloaded'});
    await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
    await expect(page.locator('.provider-wizard')).toBeVisible();
    const outside = await page.locator('.provider-wizard').evaluate(el => {
      const p=el.getBoundingClientRect();
      return [...el.querySelectorAll('input,select,button')].filter(c=>{const r=c.getBoundingClientRect();return r.width>0&&(r.left<p.left-1||r.right>p.right+1);}).map(c=>c.outerHTML);
    });
    expect(outside).toEqual([]);
    await page.evaluate(async()=>{await Promise.all(document.getAnimations().filter(a=>Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{})));});
    const results=await new AxeBuilder({page}).include('.provider-wizard').analyze();
    const failures=results.violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}));
    expect(failures).toEqual([]);
  });
}
