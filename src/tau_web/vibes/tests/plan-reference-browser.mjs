import {chromium,webkit} from 'playwright';
import {readFileSync,mkdirSync} from 'node:fs';
import {join} from 'node:path';
import {spawn} from 'node:child_process';
import assert from 'node:assert/strict';
const reference=readFileSync('../../..'+'/dev-notes/references/plan-sidebar/index.ts.reference','utf8');
const evidenceDir=process.env.TAU_PLAN_EVIDENCE_DIR;
if(evidenceDir)mkdirSync(evidenceDir,{recursive:true});
const markup=reference.split('root.innerHTML = `')[1].split('`;')[0];
const server=spawn('bun',['dev-server.js'],{env:{...process.env,TAU_VIBES_PORT:'8894'},stdio:'ignore'});
try{
 for(let i=0;i<50;i++){try{if((await fetch('http://127.0.0.1:8894')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
 for(const engine of [chromium,webkit])for(const width of [1440,390])for(const theme of ['light','dark']){
  const browser=await engine.launch();
  try{
   const page=await browser.newPage({viewport:{width,height:900}});
   await page.route('**/pinned-plan.js',r=>r.fulfill({contentType:'text/javascript',body:reference}));
   await page.route('**/editor-vendor/codemirror.js',r=>r.fulfill({contentType:'text/javascript',body:readFileSync(process.env.TAU_PLAN_REFERENCE_VENDOR||'static/js/vendor/plan-codemirror.js','utf8')}));
   await page.route('**/agent/addons/api/plan-sidebar/plan?*',r=>r.fulfill({json:{markdown:'- [x] done\n- [-] active\n- [ ] pending',updated_at:null}}));
   await page.route('**/api/**',r=>r.fulfill({json:{markdown:'- [x] done\n- [-] active\n- [ ] pending',revision:1}}));
   const head=`<html data-theme="${theme}"><link rel="stylesheet" href="/static/css/classic/base.css"><link rel="stylesheet" href="/static/css/plan-sidebar.css">`;
   await page.route('**/tau-fixture',r=>r.fulfill({contentType:'text/html',body:head+`<main id="test"></main><script type="module">
import {html,render} from '/static/js/vendor/preact-htm.js';
import {TauPlanSidebar} from '/static/js/components/tau-plan-sidebar.js';
localStorage.setItem('tau.plan.open','true');render(html\`<\${TauPlanSidebar} sessionId="fixture"/>\`,document.getElementById('test'));
</script>`}));
   await page.route('**/reference-fixture',r=>r.fulfill({contentType:'text/html',body:head+`<div class="plan-sidebar-root open has-checklist" style="--plan-sidebar-width:380px">${markup}</div><script>
document.querySelector('.plan-sidebar-panel').style.width='380px';
document.querySelector('.plan-sidebar-subtitle').textContent='fixture';
document.querySelector('.plan-sidebar-progress-label').textContent='1/3 completed';
document.querySelector('.plan-sidebar-progress-percent').textContent='33%';
document.querySelector('.plan-sidebar-progress-fill').style.width='33%';
document.querySelector('.plan-sidebar-status').textContent='Ready.';
</script>`}));
   await page.route('**/reference-live',r=>r.fulfill({contentType:'text/html',body:head+`<script>localStorage.setItem('piclaw:plan-sidebar:open','true');window.__piclaw_web={getCurrentChatJid:()=> 'fixture'};</script><script type="module" src="/pinned-plan.js"></script>`}));
   const selectors=['.plan-sidebar-panel','.plan-sidebar-header','.plan-sidebar-progress','.plan-sidebar-footer','.plan-sidebar-actions','.plan-sidebar-toggle'];
   const measure=()=>page.evaluate(selectors=>Object.fromEntries(selectors.map(s=>{const el=document.querySelector(s);if(!el)throw new Error('Missing '+s+' '+document.body.innerHTML.slice(0,300));const r=el.getBoundingClientRect();return [s,{x:r.x,y:r.y,width:r.width,height:r.height}];})),selectors);
   await page.goto('http://127.0.0.1:8894/tau-fixture');await page.locator('.cm-content').waitFor();await page.waitForTimeout(250);const actual=await measure();
   const editorMeasure=()=>page.evaluate(()=>Object.fromEntries(['.plan-sidebar-editor','.cm-content','.cm-line','.plan-sidebar-cm-checkbox-completed'].map(s=>{const r=document.querySelector(s).getBoundingClientRect();return [s,{x:r.x,y:r.y,width:r.width,height:r.height}];})));
   const tauEditor=await editorMeasure();
   if(evidenceDir){await page.locator('.cm-content').evaluate(el=>el.blur());await page.screenshot({path:join(evidenceDir,`tau-plan-${engine.name()}-${width}-${theme}.png`)});}
   await page.goto('http://127.0.0.1:8894/reference-fixture');await page.waitForTimeout(250);const expected=await measure();
   for(const selector of selectors)for(const key of ['x','y','width','height'])assert.ok(Math.abs(actual[selector][key]-expected[selector][key])<=1,`${engine.name()} ${width} ${theme}: ${selector}.${key}: ${actual[selector][key]} vs ${expected[selector][key]}`);
   {
    await page.goto('http://127.0.0.1:8894/reference-live');
    await page.locator('.cm-content').waitFor();
    await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent.includes('pending'));
    await page.waitForTimeout(250);await page.locator('.cm-content').evaluate(el=>el.blur());
    const referenceEditor=await editorMeasure();
    for(const selector of Object.keys(tauEditor))for(const key of ['x','y','width','height'])assert.ok(Math.abs(tauEditor[selector][key]-referenceEditor[selector][key])<=1,`${engine.name()} ${width} ${theme} editor ${selector}.${key}: ${tauEditor[selector][key]} vs ${referenceEditor[selector][key]}`);
    if(evidenceDir)await page.screenshot({path:join(evidenceDir,`reference-plan-${engine.name()}-${width}-${theme}.png`)});
   }
   console.log(`${engine.name()} ${width} ${theme}: pinned-reference sidebar chrome geometry passed`);
  }finally{await browser.close();}
 }
}finally{server.kill();}
