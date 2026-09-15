import {spawn} from 'node:child_process';
import {dirname,resolve} from 'node:path';
import {chromium,webkit} from 'playwright';
import assert from 'node:assert/strict';
if(!process.env.TAU_BROWSER_BIN)throw new Error('Set TAU_BROWSER_BIN to installed wheel');
const token='local-steering-fixture',base='http://127.0.0.1:8894';
for(const engine of [chromium,webkit]){
 const env={...process.env,TAU_BROWSER_TEST_AUTH_TOKEN:token,TAU_BROWSER_PORT:'8894'};delete env.PYTHONPATH;
 const server=spawn(resolve(dirname(process.env.TAU_BROWSER_BIN),'python'),[resolve('../../../tests/browser/steer-fixture-server.py')],{env,stdio:['ignore','pipe','pipe']});
 let log='';server.stdout.on('data',d=>log+=d);server.stderr.on('data',d=>log+=d);
 const request=(path,body)=>fetch(base+path,{method:body?'POST':'GET',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json','X-Tau-CSRF':'1'},...(body?{body:JSON.stringify(body)}:{})});
 let browser;
 try{
  let ready=false;for(let i=0;i<100;i++){try{if((await request('/api/sessions')).ok){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,100));}assert.ok(ready,log);
  browser=await engine.launch();const page=await browser.newPage();
  await page.addInitScript(token=>localStorage.setItem('tau.web.authToken',token),token);
  await page.goto(`${base}/?session=steer-fixture`);
  await page.getByTestId('session-switcher').waitFor();
  const queued=await request('/api/sessions/steer-fixture/queue',{content:'Steer existing persisted input'});assert.equal(queued.status,201);const item=await queued.json();
  // Reload to load durable queue before starting the live SSE run.
  await page.reload();await page.getByTestId('queue-item').waitFor();
  const runResponse=await request('/api/sessions/steer-fixture/runs',{content:'Hold until cancelled'});assert.equal(runResponse.status,202);const run=await runResponse.json();
  const button=page.getByRole('button',{name:'Steer queued message',exact:true});
  await page.waitForFunction(()=>document.querySelector('[aria-label="Steer queued message"]')?.disabled===false);
  await page.getByTestId('queue-item').hover();await button.click();
  await page.getByTestId('queue-item').waitFor({state:'detached'});
  const pending=await (await request('/api/sessions/steer-fixture/queue')).json();assert.equal(pending.queue.length,0);
  const history=await (await request('/api/sessions/steer-fixture/queue?include_consumed=true')).json();assert.equal(history.queue.length,1);assert.equal(history.queue[0].queue_id,item.queue_id);assert.ok(history.queue[0].consumed_at);
  const id=run.run?.run_id||run.run_id;assert.ok(id);await request(`/api/runs/${id}/cancel`,{});
  console.log(`${engine.name()}: installed live SSE enables steering; original queue ID consumed once`);
 }finally{await browser?.close();server.kill();await new Promise(r=>server.exitCode!==null?r():server.once('exit',r));}
}
