import {chromium,webkit} from 'playwright';
import {createServer} from 'node:http';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {PNG} from 'pngjs';
import pixelmatch from 'pixelmatch';
import AxeBuilder from '@axe-core/playwright';
const pic='/opt/piclaw/current/app/runtime/web/static',tau=process.env.TAU_VISUAL_STATIC||'static';
const engine=process.env.TAU_VISUAL_ENGINE||'chromium';
const theme=process.env.TAU_VISUAL_THEME||'light';
const widths=process.env.TAU_VISUAL_WIDTHS?process.env.TAU_VISUAL_WIDTHS.split(',').map(Number):[820,1440];
const out=process.env.TAU_VISUAL_OUT||'/workspace/tmp/tau-full-host-diffs';mkdirSync(out,{recursive:true});
const populated=process.env.TAU_VISUAL_POPULATED==='1';
const queued=process.env.TAU_VISUAL_QUEUED==='1';
const queueText=process.env.TAU_VISUAL_LONG_QUEUE==='1'?'Long queued fixture '.repeat(20)+'END-OF-QUEUE':'Queued fixture: inspect the toolbar next.';
const queueItems=[{row_id:101,queue_id:101,session_id:'web:default',chat_jid:'web:default',agent_id:'default',queue_kind:'follow_up',mode:'queued',position:0,content:queueText}];
const messages=[{message_id:1,session_id:'web:default',role:'user',content:'Compare the two interfaces.',created_at:'2026-01-01T11:58:00Z'},{message_id:2,session_id:'web:default',role:'assistant',content:'## Visual review\n\nThe **Plan sidebar** is ready for comparison.\n\n- Typography\n- Spacing\n- Controls',created_at:'2026-01-01T11:59:00Z'}];
const plan='- [x] Inspect reference\n- [-] Port sidebar\n- [ ] Verify tablet layout\n\nKnown fixture — no model execution.';
const streams=new Set();
const eventServer=createServer((request,response)=>{
 response.writeHead(200,{'Content-Type':'text/event-stream','Cache-Control':'no-cache','Access-Control-Allow-Origin':'http://fixture.local','Access-Control-Allow-Credentials':'true'});
 response.write(': connected fixture\n\n');streams.add(response);
 response.on('close',()=>streams.delete(response));
});
await new Promise(resolve=>eventServer.listen(0,'127.0.0.1',resolve));
const eventUrl=`http://127.0.0.1:${eventServer.address().port}/events`;
const browser=await (engine==='webkit'?webkit:chromium).launch();
try{
 for(const width of widths){
 for(const host of ['piclaw','tau']){
 const context=await browser.newContext({viewport:{width,height:1180},colorScheme:theme,locale:'en-US',timezoneId:'UTC'});
 const page=await context.newPage();const requests=[],errors=[],unhandled=[],networkFailures=[];let queueRemoved=false, rejectQueueRemoval=false, releaseReturn, returnDeletes=0, rejectSteer=true, steerRequests=0;
 let fixtureQueue=queueItems.map(item=>({...item}));
 if(queued)fixtureQueue.push({...queueItems[0],row_id:102,queue_id:102,position:1,content:"Second queued fixture: preserve FIFO order."});
 await page.clock.setFixedTime(new Date('2026-01-01T12:00:00Z'));
 page.on('pageerror',e=>errors.push(e.message));
 page.on('requestfailed',request=>networkFailures.push({url:request.url(),error:request.failure()?.errorText}));
 await page.addInitScript(theme=>{document.documentElement?.setAttribute('data-theme',theme);localStorage.setItem('piclaw_system_meters_enabled','true');localStorage.setItem('tau.plan.open','false');localStorage.setItem('piclaw:plan-sidebar:open','false');localStorage.setItem('vibes-theme',theme);window.__piclaw_web={getCurrentChatJid:()=> 'web:fixture'};},theme);
 await page.route('**/*',async r=>{
 const p=decodeURIComponent(new URL(r.request().url()).pathname);requests.push(p);
 if(p==='/')return r.fulfill({contentType:'text/html',body:readFileSync(host==='piclaw'?join(pic,'classic/index.html'):join(tau,'index.html'),'utf8')});
 if(p==='/fixture-plan.js')return r.fulfill({contentType:'text/javascript',body:readFileSync('../../../dev-notes/references/plan-sidebar/index.ts.reference','utf8')});
 // Shared synthetic avatar is fixture identity data, not a product asset replacement.
 if(p==='/static/icon-192.png')return r.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192"><rect width="192" height="192" rx="32" fill="#2563eb"/><circle cx="96" cy="96" r="48" fill="white"/></svg>'});
 if(p==='/manifest.json')return r.fulfill({json:{name:'Visual fixture',start_url:'/',display:'standalone',icons:[]}});
 if(p==='/sw.js'||p==='/offline-sw.js')return r.fulfill({contentType:'text/javascript',body:'/* Fixture: service worker caching intentionally disabled. */'});
 let file;
 if(p.startsWith('/static/'))file=host==='piclaw'?join(pic,p.slice(8)):join(tau,p.slice(8));
 if(host==='tau'&&['/static/extension-ui.js','/static/frontend-sdk.js','/static/widget-bridge.js'].includes(p))file=join('../static',p.slice(8));
 if(p==='/editor-vendor/codemirror.js')file='/opt/piclaw/current/app/runtime/extensions/viewers/editor/vendor/codemirror.js';
 if(file&&existsSync(file))return r.fulfill({path:file});
 if(p==='/api/sessions/web:default/queue/102/move'&&r.request().method()==='POST'){
  fixtureQueue.reverse();fixtureQueue=fixtureQueue.map((item,position)=>({...item,position}));return r.fulfill({json:fixtureQueue[0]});
 }
 if(p==='/api/sessions/web:default/queue/102'&&r.request().method()==='DELETE'){
  returnDeletes++;
  await new Promise(resolve=>{releaseReturn=resolve;});
  const item=fixtureQueue.find(item=>item.queue_id===102);fixtureQueue=fixtureQueue.filter(item=>item.queue_id!==102);return r.fulfill({json:item});
 }
 if(p==='/api/sessions/web:default/queue/101'&&r.request().method()==='DELETE'){
  if(rejectQueueRemoval)return r.fulfill({status:409,json:{error:'Queue item changed before removal'}});
  queueRemoved=true;fixtureQueue=fixtureQueue.filter(item=>item.queue_id!==101);return r.fulfill({json:queueItems[0]});
 }
 if(p==='/api/sessions/web:default/queue/101/steer'&&r.request().method()==='POST'){
  steerRequests++;if(r.request().postDataJSON()?.run_id!=='fixture-run')throw new Error('Steer run identity mismatch');
  if(rejectSteer)return r.fulfill({status:409,json:{error:'Fixture active run changed'}});
  fixtureQueue=fixtureQueue.filter(item=>item.queue_id!==101);return r.fulfill({json:{...queueItems[0],consumed_at:'2026-01-01T12:00:00Z'}});
 }
 let data={};
 if(p.includes('/plan'))data={markdown:plan,revision:1};
 else if(p==='/meters'||p==='/agent/system-metrics')data={cpu_percent:25,ram_percent:50,swap_percent:0,process_rss_bytes:104857600,cpu_history:[10,15,25],ram_history:[40,45,50],cpu_series:[10,15,25],ram_series:[40,45,50],process_memory:{rss_bytes:104857600},process_rss_series_bytes:[83886080,94371840,104857600],process_rss_history:[83886080,94371840,104857600],sample_interval_ms:2000};
 else if(p==='/api/extensions/frontend-modules')data={modules:[]};
 else if(p==='/api/sessions')data={sessions:[{session_id:'web:default',title:'Fixture session',model:'fixture',provider_name:'test',created_at:'2026-01-01T00:00:00Z'},...(process.env.TAU_VISUAL_RETURN_SWITCH==='1'?[{session_id:'other',title:'Other fixture',model:'fixture',provider_name:'test',created_at:'2026-01-01T00:00:00Z'}]:[])]};
 else if(p.startsWith('/api/sessions/other')){
  const suffix=p.slice('/api/sessions/other'.length);
  const resources={'':{session_id:'other',title:'Other fixture',model:'fixture',provider_name:'test'},'/timeline':{timeline:[]},'/queue':{queue:[]},'/runs':{runs:[]},'/approvals':{approvals:[]},'/context':{entry_count:0,message_count:0},'/plan':{markdown:'',revision:0}};
  data=resources[suffix]||{};
 }
 else if(p==='/api/sessions/web:default')data={session_id:'web:default',title:'Fixture session',model:'fixture',provider_name:'test'};
 else if(p.endsWith('/timeline'))data=host==='tau'?{timeline:populated?messages:[]}:{posts:populated?messages.map(m=>({id:m.message_id,timestamp:m.created_at,data:{type:m.role==='assistant'?'agent_response':m.role,content:m.content,session_id:m.session_id,is_bot_message:m.role==='assistant'}})).reverse():[],has_more:false};
 else if(p==='/agent/models')data={models:[{id:'fixture',name:'Fixture',provider:'test'}],current_model:'test/fixture',model:'test/fixture',provider:'test'};
 else if(p==='/api/files')data={kind:'directory',path:'',entries:[{name:'README.md',path:'README.md',kind:'file'}]};
 else if(p==='/workspace/index-status')data={status:'ready',state:'ready',indexed:true};
 else if(p==='/workspace/tree')data={root:{name:'Workspace',path:'.',type:'dir',children:[{name:'README.md',path:'README.md',type:'file'}]}};
 else if(p==='/workspace/visibility'||p==='/agent/push/presence')data={ok:true};
 else if(p==='/agent/settings/quick-actions')data={actions:[]};
 else if(p==='/agent/commands')data={commands:[]};
 else if(p==='/agent/roster')data={agents:[]};
 else if(p==='/agent/branches'||p==='/agent/active-chats')data={chats:[{chat_jid:'web:default',agent_name:'Fixture session',model:'test/fixture',status:'idle',is_active:false}]};
 else if(p==='/agent/queue-state')data={items:queued?fixtureQueue:[],count:queued?fixtureQueue.length:0};
 else if(p==='/agent/status')data={status:'idle',active_turns:[]};
 else if(p==='/agent/autoresearch/status')data={enabled:false};
 else if(p==='/agent/context'||p.endsWith('/context'))data={tokens:0,context_window:65536};
 else if(p==='/api/settings')data={agent_name:'PiClaw',agent_avatar:'/static/icon-192.png'};
 else if(p.endsWith('/runs'))data={runs:[]};
 else if(p.endsWith('/queue'))data={queue:queued?fixtureQueue:[]};
 else if(p.endsWith('/approvals'))data={approvals:[]};
 else if(p.includes('events')||p.startsWith('/sse/'))return r.continue({url:eventUrl});
 else if(p.includes('feed'))data={posts:[],has_more:false};
 else if(p.includes('chats'))data={chats:[]};
 else if(p.includes('web-entries'))data={entries:[]};
 if(Object.keys(data).length===0)unhandled.push({method:r.request().method(),path:p});
 return r.fulfill({json:data});
 });
 await page.goto(`http://127.0.0.1:${eventServer.address().port}/?session=web%3Adefault`);
 if(host==='piclaw')await page.addScriptTag({type:'module',url:`http://127.0.0.1:${eventServer.address().port}/fixture-plan.js`});
 await page.waitForTimeout(2000);
 const dismiss=page.getByRole('button',{name:'Dismiss',exact:true});if(await dismiss.isVisible())await dismiss.click();
 // This fixture explicitly compares the workspace-closed state in both hosts.
 const hideWorkspace=page.getByRole('button',{name:'Hide workspace',exact:true});
 if(await hideWorkspace.isVisible())await hideWorkspace.click();
 await page.locator('.plan-sidebar-toggle').click();
 await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent.includes('Verify tablet layout'));
 await page.evaluate(()=>document.fonts.ready);
 await page.addStyleTag({content:'*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}.cm-cursor,.cm-dropCursor{visibility:hidden!important}'});
 await page.locator('.cm-content').evaluate(el=>el.blur());
 if(queued){
  await page.getByText(queueItems[0].content,{exact:true}).first().waitFor();
  if(process.env.TAU_VISUAL_LONG_QUEUE==='1'&&!await page.locator('.compose-queue-stack-text').first().evaluate(el=>el.textContent.endsWith('END-OF-QUEUE')))throw new Error(`${host}: queue content truncated before rendering`);
 }
 if(populated)await page.getByText('Compare the two interfaces.',{exact:true}).waitFor();
 const sessionControl=page.locator('[data-testid="session-switcher"]');
 if((await sessionControl.innerText()).trim()!=='@Fixture session')throw new Error(`${host}: fixture session not selected`);
 if(networkFailures.length)throw new Error(`${host}: network failures ${JSON.stringify(networkFailures)}`);
 if((await page.locator('body').innerText()).includes('Last activity just now'))throw new Error(`${host}: idle fixture fabricated recent run activity`);
 if((await page.locator('body').innerText()).includes('Reconnecting'))throw new Error(`${host}: fixture event stream is not connected`);
 if(unhandled.length)throw new Error(`${host} unhandled requests: ${JSON.stringify(unhandled)}`);
 const modelAncestors=await page.locator('.compose-model-hint-btn').evaluate(el=>{const result=[];for(let n=el;n&&!n.classList.contains('container');n=n.parentElement){const r=n.getBoundingClientRect(),s=getComputedStyle(n);result.push({class:n.className,y:r.y,height:r.height,display:s.display,align:s.alignItems,justify:s.justifyContent,gap:s.gap});}return result;});
 const contextMarkup=await page.locator('.compose-meta-row').evaluate(el=>el.outerHTML);
 const modelMarkup=await page.locator('.compose-model-hint-btn').evaluate(el=>el.parentElement.outerHTML);
 const queueLayout=queued?await page.locator('[data-testid="queue-item"]').evaluateAll(rows=>rows.map(row=>[row,...row.querySelectorAll('.compose-queue-stack-text,.compose-queue-stack-actions,button')].map(el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return {class:el.className,text:el.textContent,x:r.x,y:r.y,width:r.width,height:r.height,color:s.color,background:s.backgroundColor,opacity:s.opacity};}))):null;
 const queueMarkup=queued?await page.getByText(queueItems[0].content,{exact:true}).first().evaluate(el=>el.closest('[data-testid="queue-item"]')?.outerHTML||el.parentElement.outerHTML):null;
 const postLayout=await page.locator('.post').evaluateAll(elements=>elements.map(el=>{const r=el.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,html:el.outerHTML};}));
 const iconMarkup=await page.evaluate(()=>Object.fromEntries(['[data-testid="hamburger"]','.compose-search-btn','.compose-location-btn','.compose-mic-btn','.voice-input-btn','.send-btn'].map(s=>[s,document.querySelector(s)?.outerHTML||null])));
 const composerControls=await page.locator('.compose-box').evaluate(el=>[...el.querySelectorAll('button,textarea')].map(n=>{const r=n.getBoundingClientRect(),s=getComputedStyle(n);return {class:n.className,label:n.getAttribute('aria-label'),text:n.textContent,x:r.x,y:r.y,width:r.width,height:r.height,border:s.border,padding:s.padding};}));
 const edgeElements=await page.evaluate(()=>[...document.elementsFromPoint(33,15)].slice(0,5).map(el=>({tag:el.tagName,class:el.className,text:el.textContent?.slice(0,60),zIndex:getComputedStyle(el).zIndex,background:getComputedStyle(el).backgroundColor})));
 const meterAncestors=await page.locator('.system-meters-card').evaluate(el=>{const result=[];for(let n=el;n;n=n.parentElement){const s=getComputedStyle(n),r=n.getBoundingClientRect();result.push({tag:n.tagName,class:n.className,x:r.x,width:r.width,position:s.position,right:s.right,transform:s.transform,filter:s.filter,contain:s.contain});}return result;});
 const layout=await page.evaluate(()=>Object.fromEntries(['.plan-sidebar-toggle','.plan-sidebar-panel','.plan-sidebar-header','.plan-sidebar-subtitle','.plan-sidebar-progress','.plan-sidebar-progress-label','.timeline','.timeline-content > div','.compose-box','.compose-box textarea','.system-meters-card','[data-testid="session-switcher"]'].map(selector=>{const el=document.querySelector(selector),r=el.getBoundingClientRect(),s=getComputedStyle(el);return [selector,{x:r.x,y:r.y,width:r.width,height:r.height,font:s.font,color:s.color,background:s.backgroundColor,padding:s.padding,gap:s.gap}];})));
 if(errors.length)throw new Error(`${host}: ${errors.join('; ')}`);
 await page.screenshot({path:join(out,`${host}-${width}.png`)});
 const meterBox=await page.locator('.system-meters-card').boundingBox();
 if(width>600&&Math.abs(meterBox.x+meterBox.width-(width-12))>1)throw new Error(`${host}: meter viewport anchor mismatch`);
 // The open Plan covers the HUD: capture its closed state separately rather than infer HUD pixels.
 await page.locator('.plan-sidebar-toggle').click();
 await page.waitForFunction(()=>!document.querySelector('.plan-sidebar-root')?.classList.contains('open'));
 await page.waitForTimeout(300);
 await page.mouse.move(Math.floor(width/2),300);
 await page.evaluate(()=>document.activeElement instanceof HTMLElement&&document.activeElement.blur());
 const closedControls=await page.evaluate(()=>Object.fromEntries(['.plan-sidebar-toggle svg','.plan-sidebar-toggle-meter','.plan-sidebar-toggle-meter-fill','[data-testid="session-switcher"] svg'].map(selector=>{const el=document.querySelector(selector);if(!el)return[selector,null];const r=el.getBoundingClientRect();return[selector,{html:el.outerHTML,x:r.x,y:r.y,width:r.width,height:r.height}];})));
 await page.screenshot({path:join(out,`${host}-${width}-plan-closed.png`)});
 if(populated){
  await page.locator('#post-2').hover();
  await page.screenshot({path:join(out,`${host}-${width}-message-hover.png`)});
  if(host==='tau'){
   await page.evaluate(()=>{window.fixtureClipboard=null;Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.fixtureClipboard=text;}}});});
   await page.locator('#post-2').getByRole('button',{name:'Copy message',exact:true}).click();
   const copied=await page.evaluate(()=>window.fixtureClipboard);
   if(copied!==messages[1].content)throw new Error('Copy did not preserve full stored message');
   await page.evaluate(()=>{
    window.fixtureSpeech=[];
    Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{speak:utterance=>window.fixtureSpeech.push(utterance.text),cancel:()=>window.fixtureSpeech.push('CANCEL')}});
    window.SpeechSynthesisUtterance=class {constructor(text){this.text=text;}};
   });
   await page.locator('#post-2').getByRole('button',{name:'Read aloud',exact:true}).click();
   await page.locator('#post-2').getByRole('button',{name:'Stop reading aloud',exact:true}).click();
   const speech=await page.evaluate(()=>window.fixtureSpeech);
   if(!speech.some(text=>text.startsWith('Visual review'))||speech.at(-1)!=='CANCEL')throw new Error('Speech start/stop failed');
  }
 }
 if(queued&&host==='tau'){
  const steerButtons=page.getByRole('button',{name:'Steer queued message',exact:true});
  if(await steerButtons.count()!==2)throw new Error('Missing queue steer controls');
  for(const button of await steerButtons.all())if(!await button.isDisabled())throw new Error('Idle queue allowed steering');
  if(process.env.TAU_VISUAL_ACTIVE_STEER==='1'){
   for(const stream of streams)stream.write('event: tau.agent.agent_start\ndata: {"session_id":"web:default","run_id":"fixture-run","payload":{}}\n\n');
   const target=page.getByTestId('queue-item').filter({hasText:queueItems[0].content});
   await page.waitForFunction(()=>!document.querySelector('[aria-label="Steer queued message"]')?.disabled);
   let failure='';page.once('dialog',async dialog=>{failure=dialog.message();await dialog.accept();});
   await target.getByRole('button',{name:'Steer queued message',exact:true}).click();
   for(let i=0;i<100&&!failure;i++)await page.waitForTimeout(10);
   if(!failure.includes('Fixture active run changed')||fixtureQueue.length!==2)throw new Error('Failed steer lost input');
   rejectSteer=false;await target.getByRole('button',{name:'Steer queued message',exact:true}).click();
   await target.waitFor({state:'detached'});if(steerRequests!==2)throw new Error('Unexpected steer count');
   for(const stream of streams)stream.write('event: tau.agent.agent_end\ndata: {"session_id":"web:default","run_id":"fixture-run","payload":{}}\n\n');
   fixtureQueue=queueItems.map(item=>({...item}));fixtureQueue.push({...queueItems[0],row_id:102,queue_id:102,position:1,content:'Second queued fixture: preserve FIFO order.'});
   await page.waitForFunction(()=>document.querySelectorAll('[data-testid="queue-item"]').length===2);
  }
  const rows=page.getByTestId('queue-item');
  await rows.nth(1).hover();await rows.nth(1).getByRole('button',{name:'Move up in queue',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('[data-testid="queue-item"]')?.textContent.includes('Second queued fixture'));
  const removingRow=rows.filter({hasText:queueItems[0].content});await removingRow.hover();
  rejectQueueRemoval=true;
  const failureDialog=page.waitForEvent('dialog');
  await removingRow.getByRole('button',{name:'Remove queued message',exact:true}).click();
  const dialog=await failureDialog;
  if(!dialog.message().includes('Queue item changed before removal'))throw new Error('Missing queue removal error');
  await dialog.accept();
  if(queueRemoved||await page.getByTestId('queue-item').count()!==2)throw new Error('Failed removal lost queued input');
  rejectQueueRemoval=false;
  await removingRow.getByRole('button',{name:'Remove queued message',exact:true}).click();
  await removingRow.waitFor({state:'detached'});
  if(!queueRemoved)throw new Error('Queue removal did not use session-scoped DELETE');
  const composer=page.locator('.compose-box textarea');
  await page.evaluate(()=>{
   window.fixtureOriginalSetItem=Storage.prototype.setItem;
   Storage.prototype.setItem=function(key,value){if(key.startsWith('tau.queue-return:'))throw new Error('Fixture storage quota');return window.fixtureOriginalSetItem.call(this,key,value);};
  });
  let storageErrorMessage='';
  page.once('dialog',async dialog=>{storageErrorMessage=dialog.message();await dialog.accept();});
  await rows.first().hover();await rows.first().getByRole('button',{name:'Return queued message to editor',exact:true}).click();
  if(!storageErrorMessage.includes('Fixture storage quota'))throw new Error('Missing storage failure report');
  if(returnDeletes!==0||await rows.count()!==1)throw new Error('Storage failure removed queued input');
  await page.evaluate(()=>{Storage.prototype.setItem=window.fixtureOriginalSetItem;delete window.fixtureOriginalSetItem;});
  await composer.fill('Existing draft');
  page.once('dialog',dialog=>dialog.accept());
  await rows.first().hover();await rows.first().getByRole('button',{name:'Return queued message to editor',exact:true}).click();
  for(let i=0;i<100&&!releaseReturn;i++)await page.waitForTimeout(10);
  if(!releaseReturn)throw new Error('Return DELETE did not start');
  await rows.first().getByRole('button',{name:'Return queued message to editor',exact:true}).click();
  if(returnDeletes!==1)throw new Error('Duplicate return issued more than one DELETE');
  await composer.fill('Newer draft written during return');
  if(process.env.TAU_VISUAL_RETURN_SWITCH==='1'){
   await page.getByTestId('session-switcher').click();
   await page.getByRole('combobox',{name:'Search sessions',exact:true}).fill('Other fixture');
   await page.getByRole('option').filter({hasText:'Other fixture'}).first().click();
   await page.waitForFunction(()=>document.querySelector('[data-testid="session-switcher"]')?.textContent.includes('Other fixture'));
   await composer.fill('Other session draft');
  }
  releaseReturn();
  await rows.waitFor({state:'detached'});
  if(process.env.TAU_VISUAL_RETURN_SWITCH==='1'){
   await page.waitForFunction(()=>JSON.parse(localStorage.getItem('vibes_compose_draft:web%3Adefault')||'{}').text==='Newer draft written during return\n\nSecond queued fixture: preserve FIFO order.');
   if(await composer.inputValue()!=='Other session draft')throw new Error('Return overwrote another session draft');
  }else await page.waitForFunction(()=>document.querySelector('.compose-box textarea')?.value==='Newer draft written during return\n\nSecond queued fixture: preserve FIFO order.');
 }
 const accessibility=process.env.TAU_VISUAL_AXE==='1'?await new AxeBuilder({page}).include('.compose-box').withRules(['color-contrast']).analyze():null;
 if(process.env.TAU_VISUAL_PICKER==='1'){
  await page.getByTestId('session-switcher').click();
  const pickerSearch=page.locator('.compose-session-search');
  await pickerSearch.waitFor();
  await page.mouse.move(Math.floor(width/2),300);
  const pickerDetails=await page.locator('.compose-session-popup').evaluate(el=>{const r=el.getBoundingClientRect();const s=getComputedStyle(el);return {x:r.x,y:r.y,width:r.width,height:r.height,boxSizing:s.boxSizing,minHeight:s.minHeight,border:s.border,padding:s.padding,children:[...el.children].map(n=>{const r=n.getBoundingClientRect(),s=getComputedStyle(n);return{class:n.className,x:r.x,y:r.y,width:r.width,height:r.height,flex:s.flex,padding:s.padding,gap:s.gap};}),text:el.innerText,html:el.outerHTML};});
  writeFileSync(join(out,`${host}-${width}-picker.json`),JSON.stringify(pickerDetails,null,2));
  await page.screenshot({path:join(out,`${host}-${width}-session-picker.png`)});
  await pickerSearch.fill('no-such-fixture-session');
  await page.waitForFunction(()=>document.querySelectorAll('.compose-session-popup [role="option"]').length===0);
  await pickerSearch.fill('');
  await page.waitForFunction(()=>document.querySelectorAll('.compose-session-popup [role="option"]').length>0);
  await page.keyboard.press('Escape');
  await pickerSearch.waitFor({state:'hidden'});
 }
 const hamburger=page.getByTestId('hamburger');
 await hamburger.click();
 await page.getByRole('menu').waitFor({state:'visible'});
 await hamburger.click();
 await page.getByRole('menu').waitFor({state:'hidden'});
 if(await hamburger.getAttribute('aria-expanded')!=='false')throw new Error(`${host}: workspace menu failed to close`);
 await hamburger.click();
 await page.getByRole('menuitem',{name:'Show workspace',exact:true}).click();
 await page.waitForFunction(()=>!document.querySelector('.app-shell')?.classList.contains('workspace-collapsed'));
 if(process.env.TAU_VISUAL_WORKSPACE==='1'){
  await page.locator('.workspace-sidebar').getByText('README.md',{exact:true}).first().waitFor();
  await page.mouse.move(width-10,300);
  const workspace=await page.locator('.workspace-sidebar').evaluate(el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return {x:r.x,y:r.y,width:r.width,height:r.height,position:s.position,header:el.querySelector('.workspace-header')?.outerHTML,text:el.innerText};});
  writeFileSync(join(out,`${host}-${width}-workspace.json`),JSON.stringify(workspace,null,2));
  await page.screenshot({path:join(out,`${host}-${width}-workspace-open.png`)});
  if(host==='tau'){
   const workspaceActions=page.getByRole('button',{name:'Workspace actions',exact:true});
   await workspaceActions.click();
   const hiddenToggle=page.getByRole('menuitem',{name:'Show hidden files',exact:true});await hiddenToggle.click();
   await workspaceActions.click();await page.getByRole('menuitem',{name:'Hide hidden files',exact:true}).waitFor();
   await page.keyboard.press('Escape');
   if(await workspaceActions.getAttribute('aria-expanded')!=='false')throw new Error('Workspace menu failed to close');
   if(!await page.locator('.workspace-header .workspace-create').isDisabled())throw new Error('Read-only workspace exposes enabled file creation');
  }
 }
 await hamburger.click();
 await page.getByRole('menuitem',{name:'Hide workspace',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('.app-shell')?.classList.contains('workspace-collapsed'));
 writeFileSync(join(out,`${host}-${width}-diagnostics.json`),JSON.stringify({requests:[...new Set(requests)],errors,unhandled,accessibility:accessibility?.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),networkFailures,closedControls,queueLayout,queueMarkup,postLayout,iconMarkup,contextMarkup,modelAncestors,modelMarkup,composerControls,edgeElements,meterAncestors,layout,sessionControl:await page.locator('[data-testid="session-switcher"]').allTextContents(),text:(await page.locator('body').innerText()).slice(0,2000)},null,2));
 await context.close();
 }
 for(const state of ['', '-plan-closed',...(populated?['-message-hover']:[]),...(process.env.TAU_VISUAL_PICKER==='1'?['-session-picker']:[]),...(process.env.TAU_VISUAL_WORKSPACE==='1'?['-workspace-open']:[])]){
 const a=PNG.sync.read(readFileSync(join(out,`piclaw-${width}${state}.png`))),b=PNG.sync.read(readFileSync(join(out,`tau-${width}${state}.png`))),diff=new PNG({width:a.width,height:a.height});
 const pixels=pixelmatch(a.data,b.data,diff.data,a.width,a.height,{threshold:0.1});writeFileSync(join(out,`diff-${width}${state}.png`),PNG.sync.write(diff));let exactPixels=0;for(let i=0;i<a.data.length;i+=4)if(a.data[i]!==b.data[i]||a.data[i+1]!==b.data[i+1]||a.data[i+2]!==b.data[i+2]||a.data[i+3]!==b.data[i+3])exactPixels++;
 const regions={};
 const sidebarLeft=Math.floor(width-(width<=760?Math.min(width*.92,420):380));
 for(const [name,x0,x1,y0,y1] of [['sidebar',sidebarLeft,width,0,1180],['sidebar-header',sidebarLeft,width,0,110],['sidebar-editor',sidebarLeft,width,110,1080],['sidebar-footer',sidebarLeft,width,1080,1180],['host-shell',0,sidebarLeft,0,1180]]){
  let exact=0;for(let y=y0;y<y1;y++)for(let x=Math.max(0,x0);x<x1;x++){const i=(y*a.width+x)*4;if(a.data[i]!==b.data[i]||a.data[i+1]!==b.data[i+1]||a.data[i+2]!==b.data[i+2]||a.data[i+3]!==b.data[i+3])exact++;}
  regions[name]={exactPixels:exact,bounds:{x0,x1,y0,y1}};
 }
 const report={engine,theme,width,populated,queued,state:state||'plan-open',pixels,exactPixels,regions,ratio:pixels/(a.width*a.height),threshold:0.1,masked:false};writeFileSync(join(out,`diff-${width}${state}.json`),JSON.stringify(report,null,2));console.log(report);
 }
 }
}finally{await browser.close();for(const response of streams)response.end();await new Promise(resolve=>eventServer.close(resolve));}
