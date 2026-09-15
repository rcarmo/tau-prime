import {spawn} from 'node:child_process';
import {chromium,webkit} from 'playwright';
import assert from 'node:assert/strict';
if(!process.env.TAU_BROWSER_BIN)throw new Error('TAU_BROWSER_BIN must point to installed candidate');
const width=Number(process.env.TAU_INSTALLED_WIDTH||1440),theme=process.env.TAU_INSTALLED_THEME||'light';
const token='plan-test-local-only',base='http://127.0.0.1:8894';
const server=spawn('node',['start-server.mjs'],{cwd:new URL('../../../../tests/browser/',import.meta.url),env:{...process.env,TAU_BROWSER_PORT:'8894',TAU_BROWSER_TEST_AUTH_TOKEN:token},stdio:'ignore'});
const request=(path,options={})=>fetch(base+path,{...options,headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json','X-Tau-CSRF':'1',...options.headers}});
try{
 let ready=false;for(let i=0;i<100;i++){try{if((await request('/api/sessions')).ok){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,100));}assert.ok(ready,'backend startup');
 for(const engine of [chromium,webkit]){
  const response=await request('/api/sessions',{method:'POST',body:JSON.stringify({title:`Plan ${engine.name()}`,model:"gpt-test",provider_name:"openai"})});assert.equal(response.status,201,response.status===201?'':await response.text());const session=await response.json();
  const browser=await engine.launch();try{
   const page=await browser.newPage({viewport:{width,height:1180},colorScheme:theme});await page.addInitScript(({token,theme})=>{localStorage.setItem('tau.web.authToken',token);localStorage.setItem('vibes-theme',theme);},{token,theme});
   await page.goto(`${base}/?session=${session.session_id}`);
   await page.getByRole('button',{name:'Open plan sidebar',exact:true}).click();
   const editor=page.locator('.plan-sidebar-editor .cm-content');await editor.waitFor();
   await page.waitForFunction(()=>document.querySelector('.plan-sidebar-actions button:last-child')?.disabled===false);
   await editor.fill('- [ ] installed draft');await page.getByRole('button',{name:'Save',exact:true}).click();
   await page.waitForFunction(()=>document.querySelector('.plan-sidebar-actions button:nth-child(3)').disabled);
   const saved=await (await request(`/api/sessions/${session.session_id}/plan`)).json();assert.equal(saved.markdown,'- [ ] installed draft');
   await editor.fill('- [ ] keep local');
   const update=await request(`/api/sessions/${session.session_id}/plan`,{method:'PUT',body:JSON.stringify({markdown:'- [x] remote',expected_revision:saved.revision})});assert.equal(update.status,200);
   await page.getByRole('button',{name:'Save',exact:true}).click();
   await page.getByText('Plan changed remotely. Refresh to reconcile; your draft is retained.',{exact:true}).waitFor();
   assert.equal(await editor.textContent(),'- [ ] keep local');
   page.once('dialog',dialog=>dialog.accept());
   await page.locator('.plan-sidebar-panel').getByRole('button',{name:'Refresh',exact:true}).click();
   await page.waitForFunction(()=>document.querySelector('.plan-sidebar-editor .cm-content')?.textContent==='- [x] remote');
   const current=await (await request(`/api/sessions/${session.session_id}/plan`)).json();
   const liveUpdate=await request(`/api/sessions/${session.session_id}/plan`,{method:'PUT',body:JSON.stringify({markdown:'- [x] live SSE update',expected_revision:current.revision})});
   assert.equal(liveUpdate.status,200);
   await page.waitForFunction(()=>document.querySelector('.plan-sidebar-editor .cm-content')?.textContent==='- [x] live SSE update');
   await page.context().setOffline(true);
   const disconnected=await (await request(`/api/sessions/${session.session_id}/plan`)).json();
   const offlineUpdate=await request(`/api/sessions/${session.session_id}/plan`,{method:'PUT',body:JSON.stringify({markdown:'- [x] changed while disconnected',expected_revision:disconnected.revision})});
   assert.equal(offlineUpdate.status,200);
   await page.context().setOffline(false);
   await page.waitForFunction(()=>document.querySelector('.plan-sidebar-editor .cm-content')?.textContent==='- [x] changed while disconnected');
   await page.getByRole('button',{name:'Close plan sidebar',exact:true}).click();
   const meters=await request('/meters');assert.equal(meters.status,200);
   if(width<=600)await page.locator('.system-meters-compact-summary').waitFor();
   else await page.waitForFunction(()=>{const value=document.querySelector('.system-meters-row.rss .system-meters-value');return value?.textContent.match(/^\d+(?:\.\d+)?[BKMGT]$/);});
   for(const content of ['First installed queue item','Second installed queue item']){
    const queued=await request(`/api/sessions/${session.session_id}/queue`,{method:'POST',body:JSON.stringify({content})});assert.equal(queued.status,201);
   }
   await page.reload();
   const rows=page.getByTestId('queue-item');await rows.nth(1).waitFor();
   await rows.nth(1).hover();await rows.nth(1).getByRole('button',{name:'Move up in queue',exact:true}).click();
   await page.waitForFunction(()=>document.querySelector('[data-testid="queue-item"]')?.textContent.includes('Second installed queue item'));
   let queue=(await (await request(`/api/sessions/${session.session_id}/queue`)).json()).queue;
   assert.equal(queue[0].content,'Second installed queue item');
   const first=rows.filter({hasText:'First installed queue item'});await first.hover();
   await first.getByRole('button',{name:'Remove queued message',exact:true}).click();await first.waitFor({state:'detached'});
   const composer=page.locator('.compose-box textarea');await composer.fill('Existing installed draft');
   page.once('dialog',dialog=>dialog.accept());await rows.first().hover();
   await rows.first().getByRole('button',{name:'Return queued message to editor',exact:true}).click();
   await rows.waitFor({state:'detached'});
   await page.waitForFunction(()=>document.querySelector('.compose-box textarea')?.value==='Existing installed draft\n\nSecond installed queue item');
   queue=(await (await request(`/api/sessions/${session.session_id}/queue`)).json()).queue;assert.equal(queue.length,0);
   console.log(`${engine.name()}: installed Plan/SSE/meters and persistent queue reorder/remove/return passed`);
  }finally{await browser.close();}
 }
}finally{server.kill();}
