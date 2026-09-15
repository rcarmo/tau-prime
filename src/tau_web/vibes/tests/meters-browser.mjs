import {chromium,webkit} from 'playwright';
import {spawn} from 'node:child_process';
import assert from 'node:assert/strict';
const server=spawn('bun',['dev-server.js'],{env:{...process.env,TAU_VIBES_PORT:'8894'},stdio:'ignore'});
try{
 for(let i=0;i<50;i++){try{if((await fetch('http://127.0.0.1:8894')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
 for(const engine of [chromium,webkit]){
  const browser=await engine.launch();
  try{
   const page=await browser.newPage({viewport:{width:1440,height:900}});let requests=0,fail=false;const errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   await page.route('**/meters',r=>{requests++;return r.fulfill(fail?{status:503,body:'unavailable'}:{json:{cpu_percent:25,ram_percent:50,swap_percent:0,process_rss_bytes:1048576,cpu_history:[0,25],ram_history:[40,50],swap_history:[0,0],process_rss_history:[524288,1048576]}});});
   await page.route('**/meters-fixture',r=>r.fulfill({contentType:'text/html',body:`<link rel="stylesheet" href="/static/css/classic/base.css"><link rel="stylesheet" href="/static/css/classic/shell.css"><main id="test"></main><script type="module">
import {html,render} from '/static/js/vendor/preact-htm.js';
import {TauMeters} from '/static/js/components/tau-meters.js';
render(html\`<\${TauMeters}/>\`,document.getElementById('test'));
</script>`}));
   await page.goto('http://127.0.0.1:8894/meters-fixture');
   await page.getByText('25%',{exact:true}).waitFor();
   assert.equal(await page.locator('.system-meters-row').count(),3);
   assert.equal(await page.locator('.system-meters-row.cpu path').getAttribute('d'),'M0.00,16.00 L56.00,12.00');
   const box=await page.locator('.system-meters-card').boundingBox();assert.ok(box.x>=0&&box.x+box.width<=1440);
   await page.setViewportSize({width:390,height:844});
   await page.getByText('CPU 25% • RAM 50%',{exact:true}).waitFor();
   assert.equal(await page.locator('.system-meters-row').count(),0);
   await page.getByRole('button',{name:'Collapse system meters',exact:true}).click();
   await page.waitForFunction(()=>localStorage.getItem('tau.meters.collapsed')==='true');
   const stopped=requests;await page.waitForTimeout(2200);assert.equal(requests,stopped);
   await page.reload();await page.getByRole('button',{name:'Expand system meters',exact:true}).waitFor();assert.equal(requests,stopped);
   fail=true;await page.getByRole('button',{name:'Expand system meters',exact:true}).click();
   await page.waitForFunction(()=>document.querySelector('.system-meters-card')?.title.includes('503'));
   assert.equal(await page.locator('.system-meters-compact-summary').textContent(),'CPU Unavailable • RAM Unavailable');
   assert.deepEqual(errors,[]);console.log(`${engine.name()}: meters samples, collapse persistence/polling, error state passed`);
  }finally{await browser.close();}
 }
}finally{server.kill();}
