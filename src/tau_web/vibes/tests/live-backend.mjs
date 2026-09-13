import {chromium,webkit,expect} from '@playwright/test';
import {spawn} from 'node:child_process';
const backend=spawn('node',['start-server.mjs'],{cwd:new URL('../../../../tests/browser/',import.meta.url),env:{...process.env,TAU_BROWSER_PORT:'8894'},stdio:'pipe'});
let log='';backend.stderr.on('data',d=>log+=d);backend.stdout.on('data',d=>log+=d);
const proxy=spawn('bun',['dev-server.js'],{cwd:new URL('..',import.meta.url),env:{...process.env,TAU_VIBES_PORT:'8893',TAU_VIBES_BACKEND:'http://127.0.0.1:8894'},stdio:'ignore'});
let browser;
try {
 for(const url of ['http://127.0.0.1:8894/api/health','http://127.0.0.1:8893/']) {
  let ready=false;
  for(let i=0;i<200;i++){try{if((await fetch(url)).ok){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,100));}
  if(!ready)throw new Error(`Server unavailable: ${url}\n${log}`);
 }
 const response=await fetch('http://127.0.0.1:8893/api/sessions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({provider_name:'test',model:'fixture',title:'Live backend session'})});
 expect(response.status).toBe(201);const session=await response.json();
 const controller=new AbortController();
 const stream=await fetch('http://127.0.0.1:8893/api/events',{signal:controller.signal});
 expect(stream.status).toBe(200);
 const reader=stream.body.getReader();let text='';
 const timeout=setTimeout(()=>controller.abort(),5000);
 try {while(!text.includes('\n\n')){const {value,done}=await reader.read();if(done)break;text+=new TextDecoder().decode(value);}expect(text).toContain('event: tau.snapshot');}
 finally{clearTimeout(timeout);controller.abort();await reader.cancel().catch(()=>{});}
 browser=await (process.env.TAU_LIVE_ENGINE==='webkit'?webkit:chromium).launch();const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(`http://127.0.0.1:8893/?session=${encodeURIComponent(session.session_id)}`);
 await expect(page.getByText('@Live backend session',{exact:true})).toBeVisible();
 await expect(page.locator('.compose-box textarea')).toBeVisible();
 await expect(page.getByText('README.md',{exact:true}).first()).toBeVisible();
 await page.getByText('README.md',{exact:true}).first().click();
 await expect(page.locator('.workspace-preview-text')).toContainText('Tau Browser Fixture');
 await page.locator('summary').filter({hasText:'Plan'}).click();
 const plan=page.getByLabel('Plan markdown');
 await expect(plan).toBeEnabled();
 await plan.fill('- [ ] Live backend plan');
 await page.getByRole('button',{name:'Save plan',exact:true}).click();
 await expect(page.getByRole('button',{name:'Save plan',exact:true})).toBeDisabled();
 const savedPlan=await (await fetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}/plan`)).json();
 expect(savedPlan.markdown).toContain('Live backend plan');
 await plan.fill('- [ ] Keep local conflict draft');
 const remoteUpdate=await fetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}/plan`,{
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
 const archived=await (await fetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}`)).json();
 expect(archived.archived_at).toBeTruthy();
 await page.getByRole('button',{name:'Restore Live backend session',exact:true}).click();
 await expect(page.getByRole('button',{name:'Archive Live backend session',exact:true})).toBeVisible();
 const restored=await (await fetch(`http://127.0.0.1:8893/api/sessions/${session.session_id}`)).json();
 expect(restored.archived_at).toBe(null);
 expect(errors).toEqual([]);
 console.log('PASS real Tau session create/list/model/timeline startup, plan save/conflict/confirmed reload, archive/restore and proxied SSE snapshot; no provider run attempted');
}finally{await browser?.close();proxy.kill();backend.kill();}
