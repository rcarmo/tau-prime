import { tauItems, fixedTime, tauMeters } from "../fixtures/visual-state.mjs";
import { expect, test } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

for (const colorScheme of ['light','dark']) {
  test(`capture populated ${colorScheme} chat and settings for review`, async ({ page }, info) => {
    await page.emulateMedia({colorScheme});
    await page.clock.setFixedTime(new Date(fixedTime));
    await page.route('**/api/events*', route=>route.fulfill({contentType:'text/event-stream',body:': fixture\n\n'}));
    await page.route('**/meters', route=>route.fulfill({contentType:'application/json',body:JSON.stringify(tauMeters)}));
    await page.goto('/',{waitUntil:'domcontentloaded'});
    await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
    const cancel=page.getByRole('button',{name:'Cancel',exact:true});
    await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});
    if(await cancel.isVisible()) await cancel.click();
    await page.evaluate(items=>window.dispatchEvent(new CustomEvent('tau:timeline-render',{detail:{selected:true,items}})),tauItems);
    await expect(page.locator('.message-list__content h2')).toHaveText('Workspace review');
    await page.locator('.message-list__tool-call-header').click();
    await expect(page.locator('.message-list__tool-call-body')).toBeVisible();
    await expect(page.locator('#meters-summary')).toHaveText('CPU 10% · RAM 25% · RSS 80 MB · Swap 0%');
    await page.evaluate(()=>document.fonts.ready);
    const dir='/workspace/tmp/tau-populated-review'; await mkdir(dir,{recursive:true});
    await page.screenshot({path:path.join(dir,`${info.project.name}-${colorScheme}-chat.png`)});
    const geometry = await page.locator('.activity-bar, .app-layout__sidebar-wrapper, .tab-bar, .chat__compose, .chat__compose-container, .chat__input, .chat__toolbar, .chat__send-btn, .app-layout__status-bar').evaluateAll(elements=>elements.map(el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return {fontSize:s.fontSize,fontFamily:s.fontFamily,verticalAlign:s.verticalAlign,whiteSpace:s.whiteSpace,padding:s.padding,margin:s.margin,display:s.display,gap:s.gap,lineHeight:s.lineHeight,className:el.className,x:r.x,y:r.y,width:r.width,height:r.height};}));
    expect(geometry.find(item=>item.className==='activity-bar').y).toBe(0);
    await writeFile(path.join(dir,`${info.project.name}-${colorScheme}-geometry.json`),JSON.stringify(geometry,null,2));
    await page.getByRole('button',{name:'Settings',exact:true}).click();
    await expect(page.locator('#panel-settings')).toBeVisible();
    await page.screenshot({path:path.join(dir,`${info.project.name}-${colorScheme}-settings.png`)});
  });
}
