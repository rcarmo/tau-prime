import { chromium } from '@playwright/test';
import { spawn } from 'node:child_process';
const server=spawn('bun',['dev-server.js'],{cwd:new URL('..',import.meta.url),env:{...process.env,TAU_VIBES_PORT:'8893'},stdio:'ignore'});
const browser=await chromium.launch();
try {
 for(let i=0;i<50;i++){try{await fetch('http://127.0.0.1:8893/');break;}catch{await new Promise(r=>setTimeout(r,100));}}
 const page=await browser.newPage(); const errors=[];const missing=new Set();
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',async route=>{
  const url=new URL(route.request().url());
  if(url.pathname==='/'||url.pathname.startsWith('/static/')) return route.continue();
  const session={session_id:'smoke',title:'Tau smoke session',provider_name:'test',model:'fixture',updated_at:'r1'};
  let data;
  if(url.pathname==='/api/sessions') data={sessions:[session]};
  else if(url.pathname==='/api/sessions/smoke') data=session;
  else if(url.pathname==='/api/sessions/smoke/timeline') data={timeline:[{message_id:1,session_id:'smoke',role:'assistant',content:'Tau persisted smoke message',created_at:'2026-09-13T19:00:00Z'}]};
  else {missing.add(url.pathname);return route.fulfill({status:501,contentType:'application/json',body:JSON.stringify({error:'Not integrated'})});}
  return route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
 });
 await page.goto('http://127.0.0.1:8893/?session=smoke');
 await page.waitForTimeout(1800);
 console.log(JSON.stringify({errors,missing:[...missing],text:(await page.locator('body').innerText()).slice(0,1800)},null,2));
 if(errors.length || !(await page.locator('body').innerText()).includes('Tau persisted smoke message') || missing.has('/api/sessions/null')) process.exitCode=1;
}finally{await browser.close();server.kill();}
