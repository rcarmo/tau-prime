import { installLiveStream } from '../fixtures/live-stream.mjs';
import { installSelectedSession } from '../fixtures/selected-session.mjs';
import { tauItems, fixedTime, tauMeters } from "../fixtures/classic-state.mjs";
import { expect, test } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

for (const colorScheme of ['light','dark']) {
  test(`capture populated ${colorScheme} chat and settings for review`, async ({ page }, info) => {
    await installSelectedSession(page);
    await installLiveStream(page, 'tau');
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
    await expect(page.locator('.post-content h2')).toHaveText('Workspace review');
    await page.locator('.agent-thinking-title button').click();
    await expect(page.locator('.agent-thinking-body')).toBeVisible();
    await expect(page.locator('.tau-queue-error')).toHaveCount(0);
    await expect(page.locator('#status-stream')).toHaveText('Live');
    await expect(page.locator('#status-stream')).toBeHidden();
    await expect(page.locator('#status-session')).toHaveText('Review session');
    await expect(page.locator('#status-model')).toHaveText('test/review-model');
    await expect(page.locator('#meters-summary')).toHaveText('CPU 10% · RAM 25% · RSS 80 MB · Swap 0%');
    await page.evaluate(()=>document.fonts.ready);
    const dir='/workspace/tmp/tau-classic-populated-review'; await mkdir(dir,{recursive:true});
    await page.screenshot({path:path.join(dir,`${info.project.name}-${colorScheme}-chat.png`)});
    const geometry = await page.locator('.app-shell, .container, .timeline, .compose-box, #compose-input, .compose-footer, #compose-submit').evaluateAll(elements=>elements.map(el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return {fontSize:s.fontSize,fontFamily:s.fontFamily,verticalAlign:s.verticalAlign,whiteSpace:s.whiteSpace,padding:s.padding,margin:s.margin,display:s.display,gap:s.gap,lineHeight:s.lineHeight,className:el.className,x:r.x,y:r.y,width:r.width,height:r.height};}));
    expect(geometry.find(item=>item.className.includes('app-shell')).y).toBe(0);
    await writeFile(path.join(dir,`${info.project.name}-${colorScheme}-geometry.json`),JSON.stringify(geometry,null,2));
    await page.getByRole('button',{name:'Open sessions',exact:true}).click();
    await page.getByRole('group',{name:'Navigation',exact:true}).getByRole('button',{name:'Workspace',exact:true}).click();
    await page.evaluate(() => window.dispatchEvent(new CustomEvent('tau:workspace-render', {detail:{
      configured:true,path:'/workspace',loading:false,notice:'',hasSelection:false,
      entries:[{name:'src',path:'/workspace/src',kind:'directory'},{name:'README.md',path:'/workspace/README.md',kind:'file'}],
      editorPath:'No file selected',editorContent:'',editorNotice:'Select a file to preview.',annotations:[],annotationCount:0,
    }})));
    await expect(page.locator('#workspace-list')).toContainText('README.md');
    await page.screenshot({path:path.join(dir,`${info.project.name}-${colorScheme}-workspace.png`)});
    await page.getByRole('button',{name:'Search',exact:true}).click();
    await page.locator('#search-input').fill('workspace');
    await page.evaluate(() => window.dispatchEvent(new CustomEvent('tau:search-render', {detail:{items:[{
      entityType:'message',entityId:'user',meta:'Review session',text:'Review the workspace and preserve the existing API.',sessionId:'visual-review',
    }]}})));
    await expect(page.locator('#search-results .tau-search-result')).toHaveCount(1);
    await page.screenshot({path:path.join(dir,`${info.project.name}-${colorScheme}-search.png`)});
    await page.getByRole('button',{name:'Settings',exact:true}).click();
    await expect(page.locator('#panel-settings')).toBeVisible();
    await page.screenshot({path:path.join(dir,`${info.project.name}-${colorScheme}-settings.png`)});
  });
}
