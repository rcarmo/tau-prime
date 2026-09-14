import {spawn} from 'node:child_process';
import {chromium,webkit,expect} from '@playwright/test';
import {requireFreePorts,requireRunning,stopChild} from './server-lifecycle.mjs';
await requireFreePorts(8894);
const token='provider-live-test-token';
const server=spawn('node',['start-server.mjs'],{cwd:new URL('../../../../tests/browser/',import.meta.url),env:{...process.env,TAU_BROWSER_PORT:'8894',TAU_BROWSER_TEST_AUTH_TOKEN:token},stdio:'ignore'});
const base='http://127.0.0.1:8894';
const request=async(path,body)=>{const r=await fetch(base+path,{method:body?'POST':'GET',headers:{Authorization:`Bearer ${token}`,'X-Tau-CSRF':'1','Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});if(!r.ok)throw new Error(`${path}: ${r.status} ${await r.text()}`);return r.json();};
let browser;
try{
 for(let i=0;i<200;i++){requireRunning(server);try{if((await fetch(base+'/api/health')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
 const session=await request('/api/sessions',{provider_name:'local-llama',model:'qwen38-gsq',title:'Local provider validation'});
 browser=await (process.env.TAU_LIVE_ENGINE==='webkit'?webkit:chromium).launch();
 const context=await browser.newContext();await context.addInitScript(t=>localStorage.setItem('tau.web.authToken',t),token);
 const page=await context.newPage();await page.goto(base+'/?session='+session.session_id);
 await expect(page.getByText('@Local provider validation',{exact:true})).toBeVisible();
 const composer=page.locator('.compose-box textarea');await expect(composer).toBeEnabled();
 await composer.fill('Use the read tool to read README.md in the current workspace. Then report the heading verbatim and finish with LOCAL_PROVIDER_OK. Do not modify any files.');await composer.press('Enter');
 console.log('After send',await page.locator('body').innerText());
 let runs;
 let lastState='';let interrupted=false;let approved=0;
 await expect.poll(async()=>{
  runs=(await request(`/api/sessions/${session.session_id}/runs`)).runs;
  const approvals=await request(`/api/sessions/${session.session_id}/approvals`);
  const state=JSON.stringify({runs,approvals});if(state!==lastState){console.log(state);lastState=state;}
  for(const approval of approvals.approvals||[]){
   if(!['read','read_file'].includes(approval.tool_name))throw new Error(`Unexpected tool requiring approval: ${approval.tool_name}`);
   if(process.env.TAU_PROVIDER_RECOVERY&&!interrupted){
    await context.setOffline(true);
    expect(await page.evaluate(()=>fetch('/api/sessions').then(()=>true,()=>false))).toBe(false);
    await page.waitForTimeout(1200);
    const pending=await request(`/api/sessions/${session.session_id}/approvals`);
    expect(pending.approvals.some(item=>item.approval_id===approval.approval_id)).toBe(true);
    await context.setOffline(false);
    await page.reload();
    await expect(page.getByText('@Local provider validation',{exact:true})).toBeVisible();
    interrupted=true;
   }
   await page.getByRole('button',{name:`Allow ${approval.tool_name}`,exact:true}).click();approved++;
  }
  return runs.some(r=>['completed','failed','cancelled'].includes(r.status));
 },{timeout:180000,intervals:[500,1000]}).toBe(true);
 const timeline=await request(`/api/sessions/${session.session_id}/timeline?limit=200`);
 console.log(JSON.stringify({engine:process.env.TAU_LIVE_ENGINE||'chromium',runs,timeline},null,2));
 expect(runs).toHaveLength(1);
 expect(approved).toBeGreaterThan(0);
 if(process.env.TAU_PROVIDER_RECOVERY)expect(interrupted).toBe(true);
 expect(runs[0].status).toBe('completed');
 expect(JSON.stringify(timeline)).toContain('LOCAL_PROVIDER_OK');
 await page.reload();await expect(page.locator('.timeline')).toContainText('LOCAL_PROVIDER_OK',{timeout:15000});
 console.log('PASS real local provider run and persisted browser reload');
}finally{await browser?.close();await stopChild(server);}
