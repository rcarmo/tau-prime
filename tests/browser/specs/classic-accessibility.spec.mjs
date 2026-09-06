import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {installSelectedSession} from '../fixtures/selected-session.mjs';
import {installLiveStream} from '../fixtures/live-stream.mjs';
for(const colorScheme of ['light','dark']) test(`classic ${colorScheme} chat and navigation accessibility`,async({page})=>{
 await installSelectedSession(page);await installLiveStream(page,'tau');await page.emulateMedia({colorScheme});
 await page.goto('/',{waitUntil:'domcontentloaded'});
 await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});if(await cancel.isVisible())await cancel.click();
 await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tau:timeline-render',{detail:{selected:true,items:[
  {id:'user',role:'user',content:'Review this workspace.',meta:'2m'},
  {id:'agent',role:'assistant',content:'## Review\n\nAPI **unchanged**.\n\n```ts\nconst ready = true;\n```',meta:'1m',toolCalls:[{id:'read',name:'read',arguments:{path:'README.md'}}]},
  {id:'result',role:'tool',toolCallId:'read',content:'Workspace read successfully.',meta:''},
 ]}})));
 await page.locator('.agent-thinking-title button').click();
 await expect(page.locator('.agent-thinking-body')).toBeVisible();
 await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tau:completion-render',{detail:{open:true,index:0,items:[{label:'/help',detail:'Show command help'}]}})));
 for(const surface of ['chat','sessions','search','settings']) {
  if(surface==='sessions')await page.getByRole('button',{name:'Open sessions',exact:true}).click();
  if(surface==='search'||surface==='settings')await page.getByRole('group',{name:'Navigation',exact:true}).getByRole('button',{name:surface==='search'?'Search':'Settings',exact:true}).click();
  await page.evaluate(async()=>{await Promise.all(document.getAnimations().filter(a=>Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{})));});
  const result=await new AxeBuilder({page}).include(surface==='chat'?'.tau-classic-chat':surface==='sessions'?'#side-panel':surface==='settings'?'.settings-dialog-overlay':`#panel-${surface}`).analyze();
  expect(result.violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),surface).toEqual([]);
 }
});

for(const colorScheme of ['light','dark']) test(`classic ${colorScheme} large-code controls stay accessible and bounded`,async({page})=>{
 await installSelectedSession(page);await installLiveStream(page,'tau');await page.emulateMedia({colorScheme});
 await page.goto('/');await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});if(await cancel.isVisible())await cancel.click();
 await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tau:timeline-render',{detail:{selected:true,items:[{id:'large-code',role:'assistant',content:'```txt\n'+('unbroken'.repeat(60)+'\n').repeat(45)+'```',meta:'1m'}]}})));
 const block=page.locator('#post-large-code .post-code-block');
 for(const expanded of [false,true]) {
  if(expanded)await block.getByRole('button',{name:/Expand code/}).click();
  await page.evaluate(async()=>{await Promise.all(document.getAnimations().filter(a=>Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{})));});
  const result=await new AxeBuilder({page}).include('#post-large-code').analyze();
  expect(result.violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))).toEqual([]);
  for(const button of await block.locator('button').all()) {
   await button.scrollIntoViewIfNeeded();const r=await button.boundingBox();
   expect(r.x).toBeGreaterThanOrEqual(0);expect(r.x+r.width).toBeLessThanOrEqual(page.viewportSize().width+1);
  }
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize().width);
 }
});
