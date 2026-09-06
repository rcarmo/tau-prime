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
  const result=await new AxeBuilder({page}).include(surface==='chat'?'.tau-classic-chat':surface==='sessions'?'#side-panel':`#panel-${surface}`).analyze();
  expect(result.violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),surface).toEqual([]);
 }
});
