import {requireFreePorts,stopChild,requireRunning} from './server-lifecycle.mjs';
import { chromium, webkit, expect } from '@playwright/test';
import { spawn } from 'node:child_process';
import {mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import AxeBuilder from '@axe-core/playwright';
await requireFreePorts(8893);
const server=spawn('bun',['dev-server.js'],{cwd:new URL('..',import.meta.url),env:{...process.env,TAU_VIBES_PORT:'8893'},stdio:'ignore'});
const engine=process.env.TAU_SMOKE_ENGINE || 'chromium';
let browser;
try {
 browser=await ({chromium,webkit}[engine]).launch();
 for(let i=0;i<50;i++){requireRunning(server);try{await fetch('http://127.0.0.1:8893/');break;}catch{await new Promise(r=>setTimeout(r,100));}}
 const size=process.env.TAU_SMOKE_SIZE || (process.env.TAU_SMOKE_PHONE?'phone':'desktop');
 const viewport={phone:{width:390,height:844},tablet:{width:820,height:1180},desktop:{width:1440,height:900}}[size];
 const context=await browser.newContext({viewport,colorScheme:process.env.TAU_SMOKE_THEME || 'light'});
 await context.addInitScript(()=>{try{localStorage.setItem('tau.web.authToken','image-test-token');}catch{}});
 const page=await context.newPage(); const errors=[];const missing=new Set();
 const scan=async(selector)=>{
  if(!process.env.TAU_SMOKE_AXE)return;
  await page.evaluate(async()=>{await Promise.all(document.getAnimations().filter(a=>Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{})));});
  const result=await new AxeBuilder({page}).include(selector).analyze();
  expect(result.violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))).toEqual([]);
 };
 const submitted=[]; let rejectSend=false; let activeRun=false; let cancelled=false; let configured=null; let rejectSetup=true; let rejectSearch=true;
 const extensionSource = `export async function activate(api) { const settings=await api.request('/api/settings'); api.mountSlot('compose_above', container=>{ const text=document.createElement('p'); text.textContent='Extension mounted: '+settings.agent_name; container.append(text); for(const [label,action] of [['Extension submit',()=>api.submit({text:'Extension message',mode:'run'})],['Extension navigate',()=>api.navigate('smoke')]]) { const button=document.createElement('button'); button.textContent=label; button.onclick=async()=>{try{await action();text.textContent=label+' accepted';}catch(error){text.textContent=error.message;}};container.append(button); } }); }`;
 const extensionIntegrity='sha256-'+createHash('sha256').update(extensionSource).digest('base64');
 let uploads=0;let snapshots=0;let selectedLeaf='leaf-a';const leafChanges=[];
 let approvalPending=true;let rejectApproval=true;const decisions=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',async route=>{
  const url=new URL(route.request().url());
  if (!['http:', 'https:'].includes(url.protocol)) return route.continue();
  if(url.pathname==='/'||url.pathname.startsWith('/static/')) return route.continue();
  if(url.pathname==='/api/media/image-fixture/content') {
   expect(route.request().headers().authorization).toBe('Bearer image-test-token');
   return route.fulfill({contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNgYPgPAAEDAQAIicLsAAAAAElFTkSuQmCC','base64')});
  }
  if(url.pathname==='/api/events') return route.fulfill({contentType:'text/event-stream',body: snapshots++ === 0 ? 'id: 1\nevent: tau.snapshot\ndata: {}\n\n' : ': fixture heartbeat\n\n'});
  const session={session_id:'smoke',title:'Tau smoke session',provider_name:'test',model:'fixture',updated_at:'r1'};
  let data;
  if(url.pathname==='/api/extensions/widgets/fixture/widget') {
   expect(route.request().headers().authorization).toBe('Bearer image-test-token');
   return route.fulfill({contentType:'text/html',body:'<!doctype html><p>Refreshed widget document</p>'});
  }
  if(url.pathname==='/api/extensions/widgets/fixture/widget/actions/check') data={acknowledged:true};
  else if(url.pathname==='/api/extensions/frontend-modules') data={modules:[{extension_id:'fixture',module_id:'mounted',sdk_version:'1.0',integrity:extensionIntegrity,asset_url:'/api/extensions/assets/fixture/module.js'}]};
  else if(url.pathname==='/api/extensions/assets/fixture/module.js') {
   expect(route.request().headers().authorization).toBe('Bearer image-test-token');
   return route.fulfill({contentType:'application/javascript',body:extensionSource});
  }
  else if(url.pathname==='/api/settings') data={agent_name:'Tau'};
  else if(url.pathname==='/dashboard') {
   const pageNumber=Number(url.searchParams.get('page')||1);
   data={page:pageNumber,total_pages:2,total_sessions:9,active_sessions:0,sessions:[{session_id:pageNumber===1?'smoke':'unavailable',title:pageNumber===1?'Dashboard first':'Dashboard unavailable',activity:'idle',model:'test/fixture',queue_count:0,summary:'Fixture summary',preview_text:''}]};
  }
  else if(url.pathname==='/meters') data={cpu_percent:12.5,ram_percent:44,swap_percent:null,process_rss_bytes:104857600};
  else if(url.pathname==='/api/media' && route.request().method()==='GET') data={media:[]};
  else if(url.pathname==='/api/media') {
   uploads++;
   expect(route.request().headers()['x-tau-csrf']).toBe('1');
   expect(route.request().postDataBuffer().toString()).toContain('attachment-fixture.txt');
   data={media_id:'uploaded-fixture',filename:'attachment-fixture.txt'};
  }
  else if(url.pathname==='/api/sessions/smoke/approvals') data={approvals:approvalPending?[{approval_id:'approval-fixture',session_id:'smoke',tool_name:'bash',description:'Run fixture command',arguments:{command:'echo fixture'}}]:[]};
  else if(url.pathname==='/api/approvals/approval-fixture') {
   decisions.push(route.request().postDataJSON());
   if(rejectApproval)return route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({error:'Fixture approval conflict'})});
   approvalPending=false;data={approval_id:'approval-fixture',decision:'deny'};
  }
  else if(url.pathname==='/api/sessions/smoke/branches') data={branches:['leaf-a','leaf-b'].map(id=>({leaf_entry_id:id,active:id===selectedLeaf,depth:2}))};
  else if(url.pathname==='/api/sessions/smoke/branches/select') {
   leafChanges.push(route.request().postDataJSON());selectedLeaf=leafChanges.at(-1).leaf_entry_id;data={session,leaf_entry_id:selectedLeaf};
  }
  else if(url.pathname==='/api/sessions/smoke/plan') data={markdown:'',revision:null};
  else if(url.pathname==='/api/search') {
   if(rejectSearch)return route.fulfill({status:400,contentType:'application/json',body:JSON.stringify({error:'Fixture invalid search'})});
   data={results:[{entity_type:'message',entity_id:'1',session_id:'smoke',text:'Matched search fixture'}]};
  }
  else if(url.pathname==='/api/onboarding') {
   if(route.request().method()==='PUT') {
    configured=route.request().postDataJSON();
    if(rejectSetup)return route.fulfill({status:400,contentType:'application/json',body:JSON.stringify({error:'Fixture provider rejection'})});
   }
   data={default_provider:'test',default_model:'fixture'};
  }
  else if(url.pathname==='/api/runs/cancel-fixture/cancel') {
   expect(route.request().method()).toBe('POST');
   cancelled=true;activeRun=false;data={accepted:true,run:{status:'cancelled'}};
  }
  else if(url.pathname==='/api/sessions/smoke/runs') {
   if(route.request().method()==='POST') {
    submitted.push(route.request().postDataJSON());
    if(rejectSend) return route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({error:'Fixture run conflict'})});
    data={run_id:'accepted-fixture',status:'pending'};
   } else data={runs:activeRun?[{run_id:'cancel-fixture',session_id:'smoke',status:'running'}]:[]};
  }
  else if(url.pathname==='/api/sessions/smoke/queue') data={queue:[
   {queue_id:11,session_id:'smoke',queue_kind:'follow_up',position:0,content:'First FIFO message'},
   {queue_id:12,session_id:'smoke',queue_kind:'follow_up',position:1,content:'Second FIFO message'},
  ]};
  else if(url.pathname==='/api/sessions') data={sessions:[session]};
  else if(url.pathname==='/api/sessions/smoke') data=session;
  else if(url.pathname==='/api/sessions/smoke/timeline') data={timeline:[
   {message_id:1,session_id:'smoke',role:'assistant',content:'Tau persisted smoke message',created_at:'2026-09-13T19:00:00Z',content_blocks_json:JSON.stringify({attachments:[{media_id:'image-fixture',filename:'fixture.png',media_type:'image/png'}]})},
   {message_id:2,session_id:'smoke',role:'assistant',content:'',created_at:'2026-09-13T19:00:01Z',content_blocks_json:JSON.stringify({tool_calls:[{id:'call-fixture',name:'bash',arguments:{command:'<img src=x onerror="window.toolInjected=true">'}}]})},
   {message_id:3,session_id:'smoke',role:'tool',content:'Fixture command failed safely',created_at:'2026-09-13T19:00:02Z',content_blocks_json:JSON.stringify({name:'bash',tool_call_id:'call-fixture',ok:false})},
  ]};
  else {missing.add(url.pathname);return route.fulfill({status:501,contentType:'application/json',body:JSON.stringify({error:'Not integrated'})});}
  return route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
 });
 await page.goto('http://127.0.0.1:8893/?session=smoke');
 await expect(page.getByText('Tau persisted smoke message',{exact:true})).toBeVisible();
 await expect(page.locator('[data-extension-slot="compose_above"]')).toContainText('Extension mounted: Tau');
 await page.evaluate(()=>{
  const target=document.querySelector('[data-extension-slot="timeline_before"]');
  window.tauExtensionUI.mountWidget(target,{extension_id:'fixture',id:'widget',title:'Widget bridge fixture',height:120,url:'/fixture'},`<body><script>addEventListener('message',e=>{if(e.data.source==='tau-host')document.body.textContent=JSON.stringify(e.data);});parent.postMessage({source:'tau-widget',version:1,extension_id:'fixture',widget_id:'widget',request_id:'check-1',kind:'action',name:'check',payload:{}},'*');<\/script>`);
 });
 await expect(page.frameLocator('iframe[title="Widget bridge fixture"]').locator('body')).toContainText('"acknowledged":true');
 await expect(page.frameLocator('iframe[title="Widget bridge fixture"]').locator('body')).toContainText('"error":null');
 await page.frameLocator('iframe[title="Widget bridge fixture"]').locator('body').evaluate(()=>parent.postMessage({source:'tau-widget',version:1,extension_id:'fixture',widget_id:'widget',request_id:'refresh-1',kind:'refresh'},'*'));
 await expect(page.frameLocator('iframe[title="Widget bridge fixture"]').locator('body')).toContainText('Refreshed widget document');
 await page.frameLocator('iframe[title="Widget bridge fixture"]').locator('body').evaluate(()=>parent.postMessage({source:'tau-widget',version:1,extension_id:'fixture',widget_id:'widget',request_id:'prefill-1',kind:'submit',mode:'prefill',text:'Widget prefilled draft'},'*'));
 await expect(page.locator('.compose-box textarea')).toHaveValue('Widget prefilled draft');
 await page.frameLocator('iframe[title="Widget bridge fixture"]').locator('body').evaluate(()=>parent.postMessage({source:'tau-widget',version:1,extension_id:'fixture',widget_id:'widget',request_id:'submit-1',kind:'submit',mode:'submit',text:'Widget submitted message'},'*'));
 await expect(page.locator('.compose-box textarea')).toHaveValue('');
 expect(submitted).toEqual([{content:'Widget submitted message'}]);submitted.length=0;
 await page.evaluate(()=>window.tauExtensionUI.removeWidget('fixture:widget'));
 const image=page.getByRole('img',{name:'fixture.png',exact:true});
 await expect(image).toBeVisible();
 await expect.poll(()=>image.evaluate(el=>el.naturalWidth)).toBe(1);
 await expect(image).toHaveAttribute('src',/^blob:/);
 const tool=page.locator('details').filter({has:page.locator('summary',{hasText:'Tool call: bash'})});
 await tool.locator('summary').click();
 await expect(tool.locator('pre')).toContainText('<img src=x');
 expect(await page.evaluate(()=>window.toolInjected)).toBeUndefined();
 await expect(page.getByText('Tool result: bash (failed)',{exact:true})).toBeVisible();
 await expect(page.getByText('Fixture command failed safely',{exact:true})).toBeVisible();
 await expect(page.locator('.compose-queue-item')).toHaveCount(2);
 await expect(page.locator('.compose-queue-text')).toHaveText(['First FIFO message','Second FIFO message']);
 for(const actions of await page.locator('.compose-queue-actions').all()) await expect(actions).toBeHidden();
 await page.locator('summary').filter({hasText:'Runtime metrics'}).click();
 const metrics=page.getByRole('region',{name:'Runtime metrics'});
 await expect(metrics).toContainText('12.5%');await expect(metrics).toContainText('100.0 MiB');await expect(metrics).toContainText('Unavailable');
 await scan('body');
 await page.locator('summary').filter({hasText:'Runtime metrics'}).click();
 if(process.env.TAU_CAPTURE_DIR){
  await mkdir(process.env.TAU_CAPTURE_DIR,{recursive:true});
  await page.screenshot({path:`${process.env.TAU_CAPTURE_DIR}/${engine}-${size}-${process.env.TAU_SMOKE_THEME||'light'}-chat.png`,fullPage:true});
 }
 const composer=page.locator('.compose-box textarea');
 await composer.fill('Extension must preserve this draft');
 await page.getByRole('button',{name:'Extension submit',exact:true}).click();
 await expect(page.getByText('Extension submit accepted',{exact:true})).toBeVisible();
 expect(submitted).toEqual([{content:'Extension message'}]);submitted.length=0;
 await expect(composer).toHaveValue('Extension must preserve this draft');
 await page.getByRole('button',{name:'Extension navigate',exact:true}).click();
 await expect(page.getByText('Extension navigate accepted',{exact:true})).toBeVisible();
 await expect(composer).toHaveValue('Extension must preserve this draft');
 await page.locator('summary').filter({hasText:'Session dashboard'}).click();
 const dashboard=page.getByRole('region',{name:'Session dashboard'});
 await expect(dashboard).toContainText('Page 1 of 2');
 await dashboard.getByRole('button',{name:'Next page',exact:true}).click();
 await expect(dashboard).toContainText('Page 2 of 2');
 await expect(dashboard.getByRole('button',{name:'Next page',exact:true})).toBeDisabled();
 page.once('dialog',dialog=>dialog.accept());await dashboard.getByRole('button',{name:'Open Dashboard unavailable',exact:true}).click();
 await expect(dashboard.getByRole('alert')).toBeVisible();await expect(dashboard).toBeVisible();
 await page.waitForTimeout(3200);
 await expect(dashboard.getByRole('alert')).toBeVisible();
 await dashboard.getByRole('button',{name:'Previous page',exact:true}).click();
 await expect(dashboard).toContainText('Page 1 of 2');
 await scan('[aria-label="Session dashboard"]');
 await page.locator('summary').filter({hasText:'Session dashboard'}).click();
 await composer.fill('Branch switch keeps draft');
 await page.locator('summary').filter({hasText:'Conversation branches'}).click();
 const branch=page.getByRole('button',{name:'Leaf leaf-b · depth 2',exact:true});
 page.once('dialog',dialog=>dialog.dismiss());await branch.click();expect(leafChanges).toEqual([]);
 page.once('dialog',dialog=>dialog.accept());await branch.click();
 await expect.poll(()=>leafChanges.length).toBe(1);expect(leafChanges[0]).toEqual({leaf_entry_id:'leaf-b'});
 await expect(page.getByRole('button',{name:'Leaf leaf-b · depth 2 (active)',exact:true})).toBeDisabled();
 await expect(composer).toHaveValue('Branch switch keeps draft');
 await page.locator('summary').filter({hasText:'Conversation branches'}).click();
 const approvals=page.getByRole('region',{name:'Tool approvals'});
 await expect(approvals).toContainText('echo fixture');
 await approvals.getByRole('button',{name:'Deny bash',exact:true}).click();
 await expect(approvals.getByRole('alert')).toHaveText('Fixture approval conflict');
 await expect(approvals.getByRole('button',{name:'Deny bash',exact:true})).toBeEnabled();
 rejectApproval=false;
 await approvals.getByRole('button',{name:'Deny bash',exact:true}).click();
 await expect(approvals.getByRole('button',{name:'Deny bash',exact:true})).toHaveCount(0);
 expect(decisions).toEqual([{decision:'deny'},{decision:'deny'}]);
 await composer.fill('Accepted browser message');
 await composer.press('Enter');
 await expect(composer).toHaveValue('');
 expect(submitted).toEqual([{content:'Accepted browser message'}]);
 rejectSend=true;
 await composer.fill('Keep rejected draft');
 await composer.press('Enter');
 await expect(page.getByText('Fixture run conflict',{exact:true})).toBeVisible();
 await expect(composer).toHaveValue('Keep rejected draft');
 expect(submitted[1]).toEqual({content:'Keep rejected draft'});
 await page.locator('.compose-box input[type="file"]').setInputFiles({name:'attachment-fixture.txt',mimeType:'text/plain',buffer:Buffer.from('fixture bytes')});
 await composer.press('Enter');
 await expect.poll(()=>submitted.length).toBe(3);
 await expect(composer).toBeEnabled();
 expect(uploads).toBe(1);
 expect(submitted[2].content).toContain('[media:uploaded-fixture]');
 await expect(composer).toHaveValue('Keep rejected draft');
 rejectSend=false;
 await composer.press('Enter');
 await expect(composer).toHaveValue('');
 expect(uploads).toBe(1);
 expect(submitted[3].content).toContain('[media:uploaded-fixture]');
 await composer.fill('Keep rejected draft');
 activeRun=true;
 const cancel=page.getByRole('button',{name:'Cancel run',exact:true});
 await expect(cancel).toBeVisible();
 await cancel.click();
 await expect(page.locator('.tau-run-control button')).toHaveCount(0);
 expect(cancelled).toBe(true);
 await page.getByRole('button',{name:'Provider setup',exact:true}).click();
 const setup=page.getByRole('dialog',{name:'Provider setup'});
 await expect(setup.getByLabel('Provider',{exact:true})).toHaveValue('test');
 await setup.getByLabel('Model',{exact:true}).fill('updated-model');
 await scan('[aria-labelledby="tau-provider-title"]');
 expect(await composer.evaluate(el=>!!el.closest('[inert]'))).toBe(true);
 await setup.getByRole('button',{name:'Save provider',exact:true}).click();
 await expect(setup.getByRole('alert')).toHaveText('Fixture provider rejection');
 await expect(setup.getByLabel('Model',{exact:true})).toHaveValue('updated-model');
 await expect(setup.getByLabel('Model',{exact:true})).toBeEnabled();
 rejectSetup=false;
 await setup.getByRole('button',{name:'Save provider',exact:true}).click();
 await expect(setup).toHaveCount(0);
 expect(await composer.evaluate(el=>!!el.closest('[inert]'))).toBe(false);
 await expect(page.getByRole('button',{name:'Provider setup',exact:true})).toBeFocused();
 expect(configured).toEqual({provider:'test',model:'updated-model'});
 await expect(composer).toHaveValue('Keep rejected draft');
 await page.locator('button[title="Search"]').click();
 await composer.fill('Matched');
 await composer.press('Enter');
 await expect(page.getByRole('alert')).toContainText('Fixture invalid search');
 rejectSearch=false;
 await composer.press('Enter');
 await expect(page.getByText('Matched search fixture',{exact:true})).toBeVisible();
 await expect(page.getByText('Fixture invalid search',{exact:true})).toHaveCount(0);
 await expect(page.getByRole('link',{name:'Open source session'})).toHaveAttribute('href','?session=smoke');
 await expect(page.getByLabel('Images',{exact:true})).toBeHidden();
 await scan('body');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
 console.log(JSON.stringify({engine,size,theme:process.env.TAU_SMOKE_THEME||'light',errors,missing:[...missing],text:(await page.locator('body').innerText()).slice(0,1800)},null,2));
 if(errors.length || missing.has('/api/sessions/null')) process.exitCode=1;
}finally{await browser?.close();await stopChild(server);}
