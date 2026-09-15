import {chromium,webkit} from 'playwright';
import {spawn} from 'node:child_process';
import assert from 'node:assert/strict';
const server=spawn('bun',['dev-server.js'],{env:{...process.env,TAU_VIBES_PORT:'8894'},stdio:'ignore'});
try{
 for(let i=0;i<50;i++){try{if((await fetch('http://127.0.0.1:8894')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
 for(const engine of [chromium,webkit]){
  const browser=await engine.launch();
  try{
   const page=await browser.newPage();const calls=[],errors=[],savedPlans=new Map();let conflict=false,delaySave=false,releaseSave,eventConnections=0;
   page.on('pageerror',e=>errors.push(e.message));
   await page.route('**/api/**',async route=>{
    if(new URL(route.request().url()).pathname==='/api/events'){
     eventConnections++;
     return route.fulfill({contentType:'text/event-stream',body:eventConnections===1?'event: tau.snapshot\ndata: {}\n\n':`id: ${eventConnections}\nevent: tau.plan.updated\ndata: {"session_id":"b","event_id":${eventConnections}}\n\n`});
    }
    const request=route.request(),path=new URL(request.url()).pathname;
    calls.push({path,method:request.method(),body:request.postDataJSON()});
    let body={};
    if(path.endsWith('/plan')){
     if(request.method()==='PUT'&&delaySave)await new Promise(resolve=>{releaseSave=resolve;});
     if(request.method()==='PUT'&&conflict)return route.fulfill({status:409,json:{error:'revision conflict'}});
     if(request.method()==='PUT')savedPlans.set(path,{markdown:request.postDataJSON().markdown,revision:2});
     body=savedPlans.get(path)||{markdown:'- [ ] task',revision:1};
    }else if(path.endsWith('/runs'))body=request.method()==='GET'?{runs:[]}:{run_id:'run',status:'pending'};
    await route.fulfill({json:body});
   });
   await page.route('**/sidebar-test',route=>route.fulfill({contentType:'text/html',body:`<link rel="stylesheet" href="/static/css/plan-sidebar.css"><main id="test"></main><script type="module">
import {html,render} from '/static/js/vendor/preact-htm.js';
import {TauPlanSidebar} from '/static/js/components/tau-plan-sidebar.js';
import {TauEventStream} from '/static/js/tau-events.js';
window.startStream=()=>{window.stream=new TauEventStream({retryMs:100,onFrame:({event,data})=>{if(event==='tau.plan.updated')window.dispatchEvent(new CustomEvent('tau:plan-updated',{detail:data}));}});window.stream.connect();};
window.mount=id=>render(html\`<\${TauPlanSidebar} sessionId=\${id}/>\`,document.getElementById('test'));
window.mount('a');</script>`}));
   await page.goto('http://127.0.0.1:8894/sidebar-test');
   await page.getByRole('button',{name:'Open plan sidebar',exact:true}).click();
   await page.locator('.cm-content').waitFor();
   await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent==='- [ ] task');
   await page.locator('.cm-content').click();await page.keyboard.press('End');await page.keyboard.type(' edited');
   conflict=true;
   await page.getByRole('button',{name:'Submit to model',exact:true}).click();
   await page.getByText('Plan changed remotely. Refresh to reconcile; your draft is retained.',{exact:true}).waitFor();
   assert.equal(calls.filter(c=>c.path==='/api/sessions/a/runs'&&c.method==='POST').length,0);
   assert.equal(await page.locator('.cm-content').textContent(),'- [ ] task edited');
   conflict=false;
   await page.getByRole('button',{name:'Submit to model',exact:true}).click();
   await page.waitForFunction(()=>!document.querySelector('.plan-sidebar-actions button:last-child').disabled);
   for(let i=0;i<100&&!calls.some(c=>c.path==='/api/sessions/a/runs'&&c.method==='POST');i++)await new Promise(r=>setTimeout(r,20));
   const save=calls.findLastIndex(c=>c.method==='PUT'),send=calls.findLastIndex(c=>c.path==='/api/sessions/a/runs'&&c.method==='POST');
   assert.ok(send>save);assert.equal(calls[save].body.expected_revision,1);
   await page.evaluate(()=>window.mount('b'));
   await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent==='- [ ] task');
   await page.locator('.cm-content').click();await page.keyboard.press('End');await page.keyboard.type(' draft');
   conflict=true;
   await page.getByRole('button',{name:'Close plan sidebar',exact:true}).click();
   await page.getByText('Plan changed remotely. Refresh to reconcile; your draft is retained.',{exact:true}).waitFor();
   assert.equal(await page.getByRole('button',{name:'Close plan sidebar',exact:true}).getAttribute('aria-expanded'),'true');
   conflict=false;
   await page.getByRole('button',{name:'Close plan sidebar',exact:true}).click();
   await page.getByRole('button',{name:'Open plan sidebar',exact:true}).waitFor();
   assert.ok(calls.some(c=>c.path==='/api/sessions/b/plan'&&c.method==='PUT'&&c.body.markdown==='- [ ] task draft'));
   await page.getByRole('button',{name:'Open plan sidebar',exact:true}).click();
   await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent==='- [ ] task draft');
   await page.locator('.cm-content').click();await page.keyboard.press('End');await page.keyboard.type(' retained');
   conflict=true;page.once('dialog',dialog=>dialog.accept());
   await page.getByRole('button',{name:'Reset',exact:true}).click();
   await page.getByText('Plan changed remotely. Refresh to reconcile; your draft is retained.',{exact:true}).waitFor();
   assert.equal(await page.locator('.cm-content').textContent(),'- [ ] task draft retained');
   conflict=false;delaySave=true;
   const sendsBefore=calls.filter(c=>c.method==='POST').length;
   await page.getByRole('button',{name:'Submit to model',exact:true}).click();
   for(let i=0;i<100&&!releaseSave;i++)await new Promise(r=>setTimeout(r,20));
   assert.ok(releaseSave);
   await page.evaluate(()=>window.mount('c'));
   await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent==='- [ ] task');
   await page.evaluate(()=>window.mount('b'));
   await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent==='- [ ] task draft retained');
   const saved=page.waitForResponse(response=>response.url().endsWith('/sessions/b/plan')&&response.request().method()==='PUT');
   delaySave=false;releaseSave();await saved;
   await page.waitForTimeout(100);
   await page.waitForFunction(()=>!document.querySelector('.plan-sidebar-actions button:last-child').disabled);
   assert.equal(await page.locator('.cm-content').textContent(),'- [ ] task draft retained');
   assert.equal(calls.filter(c=>c.method==='POST').length,sendsBefore);
   const panel=page.locator('.plan-sidebar-panel');
   const initialWidth=(await panel.boundingBox()).width;
   await page.getByRole('separator',{name:'Resize plan sidebar'}).focus();
   await page.keyboard.press('ArrowLeft');
   await page.waitForFunction(width=>Math.round(document.querySelector('.plan-sidebar-panel').getBoundingClientRect().width)===width,initialWidth+20);
   await page.waitForFunction(()=>Number(localStorage.getItem('tau.plan.width'))===400);
   const grip=await page.getByRole('separator',{name:'Resize plan sidebar'}).boundingBox();
   const beforeDrag=(await panel.boundingBox()).width;
   await page.mouse.move(grip.x+grip.width/2,grip.y+40);await page.mouse.down();
   await page.mouse.move(grip.x+grip.width/2-40,grip.y+40);await page.mouse.up();
   await page.waitForFunction(width=>Math.round(document.querySelector('.plan-sidebar-panel').getBoundingClientRect().width)===width,beforeDrag+40);
   savedPlans.set('/api/sessions/b/plan',{markdown:'- [x] remotely completed',revision:3});
   await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tau:plan-updated',{detail:{session_id:'b'}})));
   await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent==='- [x] remotely completed');
   await page.locator('.cm-content').click();await page.keyboard.press('End');await page.keyboard.type(' local');
   const readsBefore=calls.filter(c=>c.method==='GET'&&c.path.endsWith('/plan')).length;
   await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tau:plan-updated',{detail:{session_id:'b'}})));
   await page.getByText('Plan changed remotely; your draft is retained. Refresh to reconcile.',{exact:true}).waitFor();
   assert.equal(await page.locator('.cm-content').textContent(),'- [x] remotely completed local');
   assert.equal(calls.filter(c=>c.method==='GET'&&c.path.endsWith('/plan')).length,readsBefore);
   await page.setViewportSize({width:390,height:844});
   await page.waitForFunction(()=>Math.abs(document.querySelector('.plan-sidebar-panel').getBoundingClientRect().width-358.8)<2);
   await page.waitForFunction(()=>{const p=document.querySelector('.plan-sidebar-panel').getBoundingClientRect(),t=document.querySelector('.plan-sidebar-toggle').getBoundingClientRect();return Math.abs(t.right-p.left)<2;});
   const mobilePanel=await panel.boundingBox(),mobileToggle=await page.locator('.plan-sidebar-toggle').boundingBox();
   assert.ok(mobilePanel.x>=0&&mobilePanel.x+mobilePanel.width<=391);
   assert.ok(Math.abs(mobileToggle.x+mobileToggle.width-mobilePanel.x)<2);
   page.once('dialog',dialog=>dialog.accept());
   await page.getByRole('button',{name:'Refresh',exact:true}).click();
   await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent==='- [x] remotely completed');
   savedPlans.set('/api/sessions/b/plan',{markdown:'- [x] after reconnect',revision:4});
   const beforeReconnect=eventConnections;
   await page.evaluate(()=>window.startStream());
   for(let i=0;i<100&&eventConnections<beforeReconnect+2;i++)await new Promise(r=>setTimeout(r,20));
   assert.ok(eventConnections>=beforeReconnect+2,'SSE must reconnect after EOF');
   await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent==='- [x] after reconnect');
   await page.evaluate(()=>window.stream.disconnect());
   assert.deepEqual(errors,[]);console.log(`${engine.name()}: conflict blocks submit, save precedes send, session isolation passed`);
  }finally{await browser.close();}
 }
}finally{server.kill();}
