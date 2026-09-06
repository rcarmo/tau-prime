import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

for(const colorScheme of ['light','dark']) {
  test(`${colorScheme} settings has no serious accessibility violations`, async ({page})=>{
    await page.emulateMedia({colorScheme});
    await page.goto('/',{waitUntil:'domcontentloaded'});
    await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
    const cancel=page.getByRole('button',{name:'Cancel',exact:true});
    if(await cancel.isVisible()) await cancel.click();
    await page.getByRole('button',{name:'Settings',exact:true}).click();
    await expect(page.locator('#panel-settings')).toBeVisible();
    await page.evaluate(async()=>{await Promise.all(document.getAnimations().filter(a=>Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{})));});
    const results=await new AxeBuilder({page}).include('#panel-settings').analyze();
    const failures=results.violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}));
    expect(failures).toEqual([]);
  });
}
