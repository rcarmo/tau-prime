import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFileSync} from 'node:fs';
import {extname,join,normalize} from 'node:path';
import {chromium,webkit} from 'playwright';

const root=new URL('../static/',import.meta.url).pathname;
const types={'.html':'text/html','.js':'text/javascript'};
const server=createServer((req,res)=>{
 if(req.url==='/'){res.writeHead(200,{'content-type':'text/html'});res.end(`<!doctype html><body><div id="app"></div><script type="module">
 import {html,render} from '/js/vendor/preact-htm.js';
 import {AgentStatus} from '/js/components/status.js';
 window.renderStatus=status=>render(html\`<\${AgentStatus} status=\${status} draft=\${null} plan=\${null} thought=\${null} pendingRequest=\${null} turnId="run" />\`,document.querySelector('#app'));
 </script>`);return;}
 const path=normalize(join(root,decodeURIComponent(req.url)));if(!path.startsWith(root)){res.writeHead(403);res.end();return;}
 let content;try{content=readFileSync(path);}catch{res.writeHead(404);res.end();return;}
 res.writeHead(200,{'content-type':types[extname(path)]||'application/octet-stream'});res.end(content);
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
try{
 for(const [name,engine] of [['chromium',chromium],['webkit',webkit]]){
  const browser=await engine.launch({headless:false});
  try{
   const page=await browser.newPage();await page.clock.install({time:1000});
   await page.goto(`http://127.0.0.1:${server.address().port}/`);
   await page.waitForFunction(()=>typeof window.renderStatus==='function');
   await page.evaluate(()=>window.renderStatus({type:'tool_call',title:'read',detail:'{"path":"README.md"}',tool_call_id:'call-1',started_at:1000}));
   assert.equal(await page.locator('.agent-status-text').textContent(),'Running: read');
   const initial=Number.parseFloat(await page.locator('.agent-status-elapsed').textContent());
   assert.ok(initial>=0&&initial<1);
   await page.clock.fastForward(1100);
   const advanced=Number.parseFloat(await page.locator('.agent-status-elapsed').textContent());
   assert.ok(advanced-initial>=1&&advanced-initial<1.2);
   await page.evaluate(()=>window.renderStatus({type:'tool_status',title:'read',detail:'Done',tool_call_id:'call-1',started_at:1000,completed_at:2500}));
   assert.equal(await page.locator('.agent-status-elapsed').textContent(),'1.5s');
   await page.clock.fastForward(2000);assert.equal(await page.locator('.agent-status-elapsed').textContent(),'1.5s');
   console.log(`${name}: tool status identity/timing passed`);
  }finally{await browser.close();}
 }
}finally{server.close();}
