import {requireFreePorts,stopChild,requireRunning} from './server-lifecycle.mjs';
import {chromium,webkit,expect} from '@playwright/test';
import {spawn} from 'node:child_process';
import AxeBuilder from '@axe-core/playwright';
const token=process.env.TAU_LIVE_AUTH ? 'local-test-only-token' : '';
const sizes={phone:{width:390,height:844},tablet:{width:820,height:1180},desktop:{width:1440,height:900}};
const viewport=sizes[process.env.TAU_LIVE_SIZE||'desktop'];
if(!viewport)throw new Error('Unknown TAU_LIVE_SIZE');
const authFetch=(url,options={})=>fetch(url,{...options,headers:{...options.headers,...(token?{Authorization:`Bearer ${token}`}:{})}});
await requireFreePorts(8893,8894);
const backend=spawn('node',['start-server.mjs'],{cwd:new URL('../../../../tests/browser/',import.meta.url),env:{...process.env,TAU_BROWSER_PORT:'8894',TAU_BROWSER_TEST_AUTH_TOKEN:token},stdio:'pipe'});
let log='';backend.stderr.on('data',d=>log+=d);backend.stdout.on('data',d=>log+=d);
const proxy=spawn('bun',['dev-server.js'],{cwd:new URL('..',import.meta.url),env:{...process.env,TAU_VIBES_PORT:'8893',TAU_VIBES_BACKEND:'http://127.0.0.1:8894'},stdio:'ignore'});
let browser;
try {
 for(const url of ['http://127.0.0.1:8894/api/health','http://127.0.0.1:8893/']) {
  let ready=false;
  for(let i=0;i<200;i++){requireRunning(backend,proxy);try{if((await authFetch(url)).ok){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,100));}
  if(!ready)throw new Error(`Server unavailable: ${url}\n${log}`);
 }
 const response=await authFetch('http://127.0.0.1:8893/api/sessions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({provider_name:'test',model:'fixture',title:'Live backend session'})});
 expect(response.status).toBe(201);const session=await response.json();
 const secondResponse=await authFetch('http://127.0.0.1:8893/api/sessions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({provider_name:'test',model:'second-fixture',title:'Model catalogue fixture'})});
 expect(secondResponse.status).toBe(201);const secondSession=await secondResponse.json();
 const controller=new AbortController();
 const stream=await authFetch('http://127.0.0.1:8893/api/events',{signal:controller.signal});
 expect(stream.status).toBe(200);
 const reader=stream.body.getReader();let text='';
 const timeout=setTimeout(()=>controller.abort(),5000);
 try {while(!text.includes('\n\n')){const {value,done}=await reader.read();if(done)break;text+=new TextDecoder().decode(value);}expect(text).toContain('event: tau.snapshot');}
 finally{clearTimeout(timeout);controller.abort();await reader.cancel().catch(()=>{});}
 browser=await (process.env.TAU_LIVE_ENGINE==='webkit'?webkit:chromium).launch();const context=await browser.newContext({viewport,colorScheme:process.env.TAU_LIVE_THEME||'light'});await context.addInitScript(()=>{window.cspViolations=[];document.addEventListener('securitypolicyviolation',event=>window.cspViolations.push({directive:event.effectiveDirective,blocked:event.blockedURI}));});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 if(token && !process.env.TAU_LIVE_LOGIN_UI)await page.addInitScript(value=>localStorage.setItem('tau.web.authToken',value),token);
 await page.goto(`http://127.0.0.1:8893/?session=${encodeURIComponent(session.session_id)}`);
 if(token && process.env.TAU_LIVE_LOGIN_UI){
  await expect(page.getByRole('dialog',{name:'Provider setup',exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Close session picker',exact:true})).toHaveCount(0);
  await page.getByLabel('Tau bearer token',{exact:true}).fill('invalid-fixture-token');
  page.once('dialog',dialog=>dialog.accept());
  await Promise.all([page.waitForEvent('load'),page.getByRole('button',{name:'Save token and reload',exact:true}).click()]);
  await expect(page.getByRole('dialog',{name:'Provider setup',exact:true})).toBeVisible();
  await expect(page.getByLabel('Tau bearer token',{exact:true})).toHaveValue('invalid-fixture-token');
  await page.getByLabel('Tau bearer token',{exact:true}).fill(token);
  page.once('dialog',dialog=>dialog.accept());
  await page.getByRole('button',{name:'Save token and reload',exact:true}).click();
 }
 await expect(page.getByText('@Live backend session',{exact:true})).toBeVisible();
 await expect(page.locator('.connection-status')).toHaveCount(0);
 await page.evaluate(()=>window.dispatchEvent(new Event('focus')));
 await page.waitForTimeout(250);
 await expect(page.locator('.connection-status')).toHaveCount(0);
 await expect(page.locator('.compose-box textarea')).toBeVisible();
 await page.locator('summary').filter({hasText:'Runtime metrics'}).click();
 await expect(page.getByRole('region',{name:'Runtime metrics'})).toContainText('Host CPU');
 await expect(page.getByRole('region',{name:'Runtime metrics'})).toContainText('Tau process RSS');
 const thinking=await page.evaluate(async id=>{
  const api=await import('/static/js/api.js');await api.getSessionModelState(id);
  return api.changeSessionModel(id,{thinking_level:'high'});
 },session.session_id);
 expect(thinking.thinking_level).toBe('high');
 await page.locator('.compose-model-hint').click();
 const thinkingSelect=page.getByLabel('Select thinking level',{exact:true});
 await expect(thinkingSelect).toBeVisible();
 await thinkingSelect.selectOption('low');
 await expect.poll(async()=>{
  const current=await (await authFetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}`)).json();
  return current.thinking_level;
 }).toBe('low');
 const composer=page.locator('.compose-box textarea');
 // Close before editing a draft, then select another real catalogue entry.
 await page.getByRole('button',{name:'Close model picker',exact:true}).click();
 await expect(page.locator('.compose-model-hint')).toBeFocused();
 await composer.fill('Draft survives model selection');
 await expect(composer).toHaveValue('Draft survives model selection');
 await composer.evaluate(el=>{window.modelDraftInput=el;});
 await page.locator('.compose-model-hint').click();
 await page.getByRole('option',{name:'test/second-fixture',exact:true}).click();
 await expect.poll(async()=> (await (await authFetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}`)).json()).model).toBe('second-fixture');
 try { await expect(composer).toHaveValue('Draft survives model selection'); }
 catch(error){
  console.error('Model draft diagnostics',JSON.stringify(await page.evaluate(id=>({
   sameInput:window.modelDraftInput===document.querySelector('.compose-box textarea'),
   originalConnected:window.modelDraftInput?.isConnected,
   storedDraftLength:(JSON.parse(localStorage.getItem(`vibes_compose_draft:${encodeURIComponent(id)}`)||'{}').text||'').length,
   currentLength:document.querySelector('.compose-box textarea')?.value.length,
   selectedSession:new URL(location.href).searchParams.get('session'),
  }),session.session_id)));
  throw error;
 }
 await composer.fill('/thinking medium');
 await composer.press('Enter');
 await expect(composer).toHaveValue('');
 await expect.poll(async()=> (await (await authFetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}`)).json()).thinking_level).toBe('medium');
 await composer.fill('/thinking invalid');
 await composer.press('Enter');
 await expect(page.getByText('Invalid Tau thinking level',{exact:true})).toBeVisible();
 await expect(composer).toHaveValue('/thinking invalid');
 const runs=await (await authFetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}/runs`)).json();
 expect(runs.runs).toHaveLength(0);
 const entries=await (await authFetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}/entries`)).json();
 const firstEntry=entries.entries.find(entry=>entry.type!=='leaf');
 expect(firstEntry?.id).toBeTruthy();
 const branchChange=await authFetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}/branches/select`,{method:'POST',headers:{'Content-Type':'application/json','X-Tau-CSRF':'1'},body:JSON.stringify({leaf_entry_id:firstEntry.id})});
 expect(branchChange.status).toBe(200);
 await page.locator('summary').filter({hasText:'Conversation branches'}).click();
 await page.getByRole('button',{name:'Refresh branches',exact:true}).click();
 const inactiveLeaf=page.getByRole('region',{name:'Conversation branches'}).getByRole('button',{name:/^Leaf /}).filter({hasNotText:'(active)'}).first();
 await expect(inactiveLeaf).toBeVisible();
 page.once('dialog',dialog=>dialog.accept());
 await inactiveLeaf.click();
 await expect.poll(async()=> (await (await authFetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}`)).json()).active_leaf_entry_id).not.toBe(firstEntry.id);
 await expect(composer).toHaveValue('/thinking invalid');
 await authFetch(`http://127.0.0.1:8893/api/sessions/${secondSession.session_id}`,{method:'DELETE'});
 const mediaCheck=await page.evaluate(async sessionId=>{
  const {uploadMedia}=await import('/static/js/api.js');
  const content='Real media fixture: café 日本語';
  const media=await uploadMedia(new File([content],'live-media.txt',{type:'text/plain'}),{sessionId});
  const unauthorized=await fetch(media.content_url);
  const token=localStorage.getItem('tau.web.authToken');
  const response=await fetch(media.content_url,{headers:token?{Authorization:`Bearer ${token}`}:{}});
  return {unauthorizedStatus:unauthorized.status,id:media.id,sessionId:media.session_id,filename:media.filename,status:response.status,content:await response.text()};
 },session.session_id);
 expect(mediaCheck.sessionId).toBe(session.session_id);
 expect(mediaCheck.filename).toBe('live-media.txt');expect(mediaCheck.status).toBe(200);
 expect(mediaCheck.content).toBe('Real media fixture: café 日本語');
 expect(mediaCheck.id).toBeTruthy();
 await page.locator('summary').filter({hasText:'Session media'}).click();
 await page.getByRole('button',{name:'Refresh media',exact:true}).click();
 const downloadEvent=page.waitForEvent('download');
 await page.getByRole('button',{name:'Download live-media.txt',exact:true}).click();
 const downloaded=await downloadEvent;
 expect(downloaded.suggestedFilename()).toBe('live-media.txt');
 const {readFile}=await import('node:fs/promises');
 expect(await readFile(await downloaded.path(),'utf8')).toBe('Real media fixture: café 日本語');
 if(token)expect(mediaCheck.unauthorizedStatus).toBe(401);
 const showWorkspace=page.getByRole('button',{name:'Show workspace',exact:true});
 if(await showWorkspace.isVisible())await showWorkspace.click();
 await expect(page.getByText('README.md',{exact:true}).first()).toBeVisible();
 await page.getByText('README.md',{exact:true}).first().click();
 await expect(page.locator('.workspace-preview-text')).toContainText('Tau Browser Fixture');
 if(viewport.width<1024)await page.getByRole('button',{name:'Hide workspace',exact:true}).click();
 await page.locator('summary').filter({hasText:'Plan'}).click();
 const plan=page.getByLabel('Plan markdown');
 await expect(plan).toBeEnabled();
 await plan.fill('- [ ] Live backend plan');
 await page.getByRole('button',{name:'Save plan',exact:true}).click();
 await expect(page.getByRole('button',{name:'Save plan',exact:true})).toBeDisabled();
 const savedPlan=await (await authFetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}/plan`)).json();
 expect(savedPlan.markdown).toContain('Live backend plan');
 await plan.fill('- [ ] Keep local conflict draft');
 const remoteUpdate=await authFetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}/plan`,{
  method:'PUT',headers:{'Content-Type':'application/json','X-Tau-CSRF':'1'},
  body:JSON.stringify({markdown:'- [ ] Remote changed plan',expected_revision:savedPlan.revision}),
 });
 expect(remoteUpdate.status).toBe(200);
 await page.getByRole('button',{name:'Save plan',exact:true}).click();
 await expect(page.getByRole('alert').filter({hasText:'Plan changed on the server'})).toBeVisible();
 await expect(plan).toHaveValue('- [ ] Keep local conflict draft');
 page.once('dialog',dialog=>dialog.dismiss());
 await page.getByRole('button',{name:'Reload plan',exact:true}).click();
 await expect(plan).toHaveValue('- [ ] Keep local conflict draft');
 page.once('dialog',dialog=>dialog.accept());
 await page.getByRole('button',{name:'Reload plan',exact:true}).click();
 await expect(plan).toHaveValue(/Remote changed plan/);
 await page.getByText('@Live backend session',{exact:true}).click();
 await page.getByRole('button',{name:'Archive Live backend session',exact:true}).click();
 await expect(page.getByRole('button',{name:'Restore Live backend session',exact:true})).toBeVisible();
 await expect.poll(async()=>new URL(page.url()).searchParams.get('session')).toBe(null);
 const archived=await (await authFetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}`)).json();
 expect(archived.archived_at).toBeTruthy();
 await page.getByRole('button',{name:'Restore Live backend session',exact:true}).click();
 await expect(page.getByRole('button',{name:'Archive Live backend session',exact:true})).toBeVisible();
 const restored=await (await authFetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}`)).json();
 expect(restored.archived_at).toBe(null);
 const onboarding=await (await authFetch('http://127.0.0.1:8893/api/onboarding')).json();
 expect(onboarding.default_provider).toBeTruthy();expect(onboarding.default_model).toBeTruthy();
 await expect(page.getByRole('button',{name:'New branch',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'New root session…',exact:true}).click();
 const newDialog=page.getByRole('dialog',{name:'New session',exact:true});
 await newDialog.getByLabel('Session name',{exact:true}).fill('Created through imported dialog');
 await newDialog.getByRole('button',{name:'Create',exact:true}).click();
 await expect(newDialog).toHaveCount(0);
 await expect(page.getByText('@Created through imported dialog',{exact:true})).toBeVisible();
 const newId=new URL(page.url()).searchParams.get('session');
 const created=await (await authFetch(`http://127.0.0.1:8893/api/sessions/${newId}`)).json();
 expect(created.provider_name).toBe(onboarding.default_provider);expect(created.model).toBe(onboarding.default_model);
 await expect(composer).toHaveValue('');
 await composer.fill('New session draft remains local');
 const planSummary=page.locator('summary').filter({hasText:/^Plan$/});
 if(!await plan.isVisible())await planSummary.click();
 await expect(plan).toBeEnabled();await plan.fill('- [ ] Unsaved new-session plan');
 await page.getByText('@Created through imported dialog',{exact:true}).click();
 await page.getByRole('option').filter({hasText:'Live backend session'}).click();
 await expect(composer).toHaveValue('/thinking invalid');
 await page.getByText('@Live backend session',{exact:true}).click();
 await page.getByRole('option').filter({hasText:'Created through imported dialog'}).click();
 await expect(composer).toHaveValue('New session draft remains local');
 if(!await plan.isVisible())await planSummary.click();
 await expect(plan).toHaveValue('- [ ] Unsaved new-session plan');
 const dashboardSummary=page.locator('summary').filter({hasText:'Session dashboard'});
 await dashboardSummary.click();
 const dashboard=page.getByRole('region',{name:'Session dashboard'});
 await expect(dashboard.getByRole('button',{name:'Open Live backend session',exact:true})).toBeVisible();
 page.once('dialog',dialog=>dialog.dismiss());
 await dashboard.getByRole('button',{name:'Open Live backend session',exact:true}).click();
 await expect(dashboard).toBeVisible();expect(new URL(page.url()).searchParams.get('session')).toBe(newId);
 page.once('dialog',dialog=>dialog.accept());
 await dashboard.getByRole('button',{name:'Open Live backend session',exact:true}).click();
 await expect(dashboard).toBeHidden();await expect(composer).toHaveValue('/thinking invalid');
 await dashboardSummary.click();page.once('dialog',dialog=>dialog.accept());
 await dashboard.getByRole('button',{name:'Open Created through imported dialog',exact:true}).click();
 await expect(dashboard).toBeHidden();await expect(composer).toHaveValue('New session draft remains local');
 if(!await plan.isVisible())await planSummary.click();
 await expect(plan).toHaveValue('- [ ] Unsaved new-session plan');
 if(process.env.TAU_LIVE_AXE){
  for(const selector of ['.tau-plan','[aria-label="Session media"]','[aria-label="Session dashboard"]','[aria-label="Runtime metrics"]']){
   const region=page.locator(selector);
   const details=region.locator('xpath=ancestor::details[1]');
   if(await details.count() && !(await details.evaluate(el=>el.open)))await details.locator('summary').click();
   await expect(region).toBeVisible();
   const result=await new AxeBuilder({page}).include(selector).analyze();
   expect(result.violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))).toEqual([]);
  }
 }
 if(process.env.TAU_LIVE_OFFLINE){
  await page.evaluate(async()=>{await navigator.serviceWorker.register('/offline-sw.js',{scope:'/'});await navigator.serviceWorker.ready;});
  await expect.poll(()=>page.evaluate(()=>!!navigator.serviceWorker.controller)).toBe(true);
  await context.setOffline(true);
  await page.reload();
  await expect(page.locator('.app-shell')).toBeVisible();
  await expect(page.getByRole('alert').first()).toBeVisible();
  expect(await page.evaluate(()=>fetch('/api/sessions').then(()=>true,()=>false))).toBe(false);
  await context.setOffline(false);
  await page.reload();
  await expect(page.locator('.app-shell')).toBeVisible();
 }
 if(token && process.env.TAU_LIVE_LOGIN_UI){
  await page.getByRole('button',{name:'Provider setup',exact:true}).click();
  if(process.env.TAU_LIVE_AXE){
   await expect(page.getByLabel('Model',{exact:true})).toBeEnabled();
   const result=await new AxeBuilder({page}).include('[aria-labelledby="tau-provider-title"]').analyze();
   expect(result.violations.filter(v=>['serious','critical'].includes(v.impact)).map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))).toEqual([]);
  }
  page.once('dialog',dialog=>dialog.accept());
  await Promise.all([page.waitForEvent('load'),page.getByRole('dialog',{name:'Provider setup',exact:true}).evaluate(form=>{
   const input=form.querySelector('input[type="password"]');
   input.value='';input.dispatchEvent(new Event('input',{bubbles:true}));
   [...form.querySelectorAll('button')].find(button=>button.textContent==='Save token and reload').click();
  })]);
  try {
   await expect(page.getByRole('dialog',{name:'Provider setup',exact:true})).toBeVisible();
  } catch(error) {
   // Record bounded, non-secret auth/bootstrap evidence before fixture teardown.
   console.error('Logout diagnostics',JSON.stringify(await page.evaluate(async()=>({
    readyState:document.readyState,
    tokenPresent:!!localStorage.getItem('tau.web.authToken'),
    sessionStatus:await fetch('/api/sessions').then(r=>r.status).catch(()=>null),
    dialogs:[...document.querySelectorAll('[role="dialog"]')].map(el=>({label:el.getAttribute('aria-label'),labelledby:el.getAttribute('aria-labelledby')})),
    alerts:[...document.querySelectorAll('[role="alert"]')].map(el=>el.textContent?.slice(0,300)),
   }))));
   throw error;
  }
  expect(await page.evaluate(()=>localStorage.getItem('tau.web.authToken'))).toBe(null);
  expect(await page.evaluate(async()=> (await fetch('/api/sessions')).status)).toBe(401);
 }
 if(process.env.TAU_VIBES_TEST_CSP)expect(await page.evaluate(()=>window.cspViolations)).toEqual([]);
 expect(errors).toEqual([]);
 console.log('PASS real Tau session create/list/model/timeline startup, plan save/conflict/confirmed reload, archive/restore and proxied SSE snapshot; no provider run attempted');
}finally{await browser?.close();await stopChild(proxy);await stopChild(backend);}
