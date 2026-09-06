import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {mkdir} from 'node:fs/promises';

for(const colorScheme of ['light','dark']) {
  test(`${colorScheme} settings has no serious accessibility violations`, async ({page},info)=>{
    await page.emulateMedia({colorScheme});
    await page.goto('/',{waitUntil:'domcontentloaded'});
    await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
    const cancel=page.getByRole('button',{name:'Cancel',exact:true});
    await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});
    if(await cancel.isVisible())await cancel.click();
    await page.getByRole('button',{name:'Open sessions',exact:true}).click();
    await page.getByRole('button',{name:'Settings',exact:true}).click();
    await expect(page.locator('#panel-settings')).toBeVisible();
    await page.evaluate(async()=>{await Promise.all(document.getAnimations().filter(a=>Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{})));});
    for (const category of ['Authentication','Model','Runtime']) {
      await page.getByRole('link',{name:category,exact:true}).click();
      const results=await new AxeBuilder({page}).include('.settings-dialog-overlay').analyze();
      const failures=results.violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}));
      expect(failures,category).toEqual([]);
    }
    await page.getByRole('link',{name:'Authentication',exact:true}).click();
    await mkdir('/workspace/tmp/tau-classic-settings-dialog',{recursive:true});
    await page.screenshot({path:`/workspace/tmp/tau-classic-settings-dialog/${info.project.name}-${colorScheme}.png`});
  });
}
