import { chromium, webkit, expect } from '@playwright/test';
import { spawn } from 'node:child_process';
const server=spawn('bun',['dev-server.js'],{cwd:new URL('..',import.meta.url),env:{...process.env,TAU_VIBES_PORT:'8893'},stdio:'ignore'});
const engine=process.env.TAU_SMOKE_ENGINE || 'chromium';
const browser=await ({chromium,webkit}[engine]).launch();
try {
 for(let i=0;i<50;i++){try{await fetch('http://127.0.0.1:8893/');break;}catch{await new Promise(r=>setTimeout(r,100));}}
 const page=await browser.newPage({viewport:process.env.TAU_SMOKE_PHONE ? {width:390,height:844} : {width:1440,height:900}}); const errors=[];const missing=new Set();
 const submitted=[]; let rejectSend=false; let activeRun=false; let cancelled=false;
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',async route=>{
  const url=new URL(route.request().url());
  if(url.pathname==='/'||url.pathname.startsWith('/static/')) return route.continue();
  if(url.pathname==='/api/events') return route.fulfill({contentType:'text/event-stream',body:'id: 1\nevent: tau.snapshot\ndata: {}\n\n'});
  const session={session_id:'smoke',title:'Tau smoke session',provider_name:'test',model:'fixture',updated_at:'r1'};
  let data;
  if(url.pathname==='/api/runs/cancel-fixture/cancel') {
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
  else if(url.pathname==='/api/sessions/smoke/timeline') data={timeline:[{message_id:1,session_id:'smoke',role:'assistant',content:'Tau persisted smoke message',created_at:'2026-09-13T19:00:00Z'}]};
  else {missing.add(url.pathname);return route.fulfill({status:501,contentType:'application/json',body:JSON.stringify({error:'Not integrated'})});}
  return route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
 });
 await page.goto('http://127.0.0.1:8893/?session=smoke');
 await expect(page.getByText('Tau persisted smoke message',{exact:true})).toBeVisible();
 await expect(page.locator('.compose-queue-item')).toHaveCount(2);
 await expect(page.locator('.compose-queue-text')).toHaveText(['First FIFO message','Second FIFO message']);
 for(const actions of await page.locator('.compose-queue-actions').all()) await expect(actions).toBeHidden();
 const composer=page.locator('.compose-box textarea');
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
 activeRun=true;
 const cancel=page.getByRole('button',{name:'Cancel run',exact:true});
 await expect(cancel).toBeVisible();
 await cancel.click();
 await expect(page.locator('.tau-run-control button')).toHaveCount(0);
 expect(cancelled).toBe(true);
 await expect(composer).toHaveValue('Keep rejected draft');
 console.log(JSON.stringify({engine,errors,missing:[...missing],text:(await page.locator('body').innerText()).slice(0,1800)},null,2));
 if(errors.length || !(await page.locator('body').innerText()).includes('Tau persisted smoke message') || missing.has('/api/sessions/null')) process.exitCode=1;
}finally{await browser.close();server.kill();}
