import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {chromium,webkit,expect} from '@playwright/test';
import {requireFreePorts} from './server-lifecycle.mjs';
await requireFreePorts(8893);
const requests=[];
const fullApp=process.env.TAU_OFFLINE_APP==='1';
const worker=await readFile(new URL('../static/offline-sw.js',import.meta.url),'utf8');
const manifest=JSON.parse(worker.match(/const SHELL = (.*);/)[1]);
let nextVersion=false;
const server=createServer(async(req,res)=>{
 requests.push({url:req.url,cookie:req.headers.cookie||'',authorization:req.headers.authorization||''});
 if(req.url==='/sw.js'){res.writeHead(200,{'Content-Type':'text/javascript','Service-Worker-Allowed':'/'});res.end(nextVersion?worker.replace(manifest.version,manifest.version+'-next'):worker);return;}
 if(req.url==='/'){res.writeHead(200,{'Content-Type':'text/html'});res.end(fullApp?await readFile(new URL('../static/index.html',import.meta.url),'utf8'):'<!doctype html><title>Public offline fixture</title><p>Public shell</p>');return;}
 if(manifest.assets.includes(req.url)){
  const path=req.url.split('?')[0];
  const independent=['/static/extension-ui.js','/static/frontend-sdk.js','/static/widget-bridge.js'].includes(path);
  try{const bytes=await readFile(new URL(independent?'../../static/'+path.slice(8):'../static/'+path.slice(8),import.meta.url));res.writeHead(200,{'Content-Type':path.endsWith('.js')?'text/javascript':path.endsWith('.css')?'text/css':'application/octet-stream'});res.end(bytes);}catch{res.writeHead(404);res.end();}return;
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
 const precache=requests.filter(request=>manifest.assets.includes(request.url)&&(!fullApp||!request.cookie));
 expect(precache.length).toBe(manifest.assets.length);
 expect(precache.every(request=>!request.cookie&&!request.authorization)).toBe(true);
 await page.evaluate(()=>fetch('/api/private').catch(()=>{}));
 const keys=await page.evaluate(async()=>{const name=(await caches.keys()).find(key=>key.startsWith('tau-vibes-shell-'));return (await (await caches.open(name)).keys()).map(request=>new URL(request.url).pathname);});
 expect(keys.some(key=>key.startsWith('/api/'))).toBe(false);
 await context.setOffline(true);
 await page.goto('http://127.0.0.1:8893/?session=private');
 await expect(fullApp?page.locator('.app-shell'):page.getByText('Public shell',{exact:true})).toBeVisible();
 expect(await page.evaluate(()=>fetch('/api/private').then(()=>true,()=>false))).toBe(false);
 if(fullApp){
  await expect(page.getByRole('alert').first()).toBeVisible();
  const composer=page.locator('.compose-box textarea');
  await composer.fill('Offline unsent draft');await composer.press('Enter');
  await expect(composer).toHaveValue('Offline unsent draft');
  await expect(page.getByRole('alert').first()).toBeVisible();
 }
 await context.setOffline(false);
 nextVersion=true;
 await page.evaluate(async()=>{const registration=await navigator.serviceWorker.getRegistration();await registration.update();});
 await expect.poll(()=>page.evaluate(async()=>!!(await navigator.serviceWorker.getRegistration()).waiting)).toBe(true);
 expect(await page.evaluate(()=>caches.keys())).toContain(`tau-vibes-shell-${manifest.version}`);
 // No skipWaiting: the old controlled page remains usable until it closes.
 await expect(fullApp?page.locator('.app-shell'):page.getByText('Public shell',{exact:true})).toBeVisible();
 await page.close();
 const upgraded=await context.newPage();
 await upgraded.goto('http://127.0.0.1:8893/');
 await expect.poll(()=>upgraded.evaluate(()=>caches.keys())).not.toContain(`tau-vibes-shell-${manifest.version}`);
 const upgradedCaches=await upgraded.evaluate(()=>caches.keys());
 expect(upgradedCaches).toContain(`tau-vibes-shell-${manifest.version}-next`);
 expect(upgradedCaches).toContain('unrelated-cache');
 console.log(`PASS credential-free precache, offline fallback and waiting-worker upgrade (${fullApp?'actual app bootstrap, unavailable backend':'isolated document'})`);
}finally{await browser?.close();server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
