import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {chromium,webkit,expect} from '@playwright/test';
import {requireFreePorts} from './server-lifecycle.mjs';
await requireFreePorts(8893);
const requests=[];
const worker=await readFile(new URL('../static/offline-sw.js',import.meta.url),'utf8');
const manifest=JSON.parse(worker.match(/const SHELL = (.*);/)[1]);
const server=createServer(async(req,res)=>{
 requests.push({url:req.url,cookie:req.headers.cookie||'',authorization:req.headers.authorization||''});
 if(req.url==='/sw.js'){res.writeHead(200,{'Content-Type':'text/javascript','Service-Worker-Allowed':'/'});res.end(worker);return;}
 if(req.url==='/'){res.writeHead(200,{'Content-Type':'text/html'});res.end('<!doctype html><title>Public offline fixture</title><p>Public shell</p>');return;}
 if(manifest.assets.includes(req.url)){
  const path=req.url.split('?')[0];
  const independent=['/static/extension-ui.js','/static/frontend-sdk.js','/static/widget-bridge.js'].includes(path);
  try{const bytes=await readFile(new URL(independent?'../../static/'+path.slice(8):'../static/'+path.slice(8),import.meta.url));res.writeHead(200);res.end(bytes);}catch{res.writeHead(404);res.end();}return;
 }
 res.writeHead(404);res.end();
});
await new Promise(resolve=>server.listen(8893,'127.0.0.1',resolve));
let browser;
try{
 browser=await (process.env.TAU_WORKER_ENGINE==='webkit'?webkit:chromium).launch();
 const context=await browser.newContext();const page=await context.newPage();
 await context.addCookies([{name:'private-cookie',value:'fixture',url:'http://127.0.0.1:8893'}]);
 await page.goto('http://127.0.0.1:8893/');requests.length=0;
 await page.evaluate(async()=>{
  for(const name of ['tau-web-shell-v12','tau-vibes-shell-old','unrelated-cache']){
   const cache=await caches.open(name);await cache.put('/sentinel',new Response(name));
  }
  await navigator.serviceWorker.register('/sw.js');await navigator.serviceWorker.ready;
 });
 await expect.poll(()=>page.evaluate(()=>!!navigator.serviceWorker.controller)).toBe(true);
 const cacheNames=await page.evaluate(()=>caches.keys());
 expect(cacheNames).toContain('unrelated-cache');
 expect(cacheNames).not.toContain('tau-web-shell-v12');
 expect(cacheNames).not.toContain('tau-vibes-shell-old');
 expect(await page.evaluate(async()=> (await (await caches.open('unrelated-cache')).match('/sentinel')).text())).toBe('unrelated-cache');
 const precache=requests.filter(request=>manifest.assets.includes(request.url));
 expect(precache.length).toBe(manifest.assets.length);
 expect(precache.every(request=>!request.cookie&&!request.authorization)).toBe(true);
 await page.evaluate(()=>fetch('/api/private').catch(()=>{}));
 const keys=await page.evaluate(async()=>{const name=(await caches.keys()).find(key=>key.startsWith('tau-vibes-shell-'));return (await (await caches.open(name)).keys()).map(request=>new URL(request.url).pathname);});
 expect(keys.some(key=>key.startsWith('/api/'))).toBe(false);
 await context.setOffline(true);
 await page.goto('http://127.0.0.1:8893/?session=private');
 await expect(page.getByText('Public shell',{exact:true})).toBeVisible();
 expect(await page.evaluate(()=>fetch('/api/private').then(()=>true,()=>false))).toBe(false);
 console.log('PASS browser credential-free precache and public-shell-only offline fallback (isolated document, not app bootstrap)');
}finally{await browser?.close();server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
