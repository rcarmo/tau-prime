import {chromium,webkit,expect} from '@playwright/test';
import {spawn} from 'node:child_process';
import {requireFreePorts,stopChild,requireRunning} from './server-lifecycle.mjs';
await requireFreePorts(8893);
const server=spawn('bun',['dev-server.js'],{cwd:new URL('..',import.meta.url),env:{...process.env,TAU_VIBES_PORT:'8893'},stdio:'ignore'});
let browser;
try {
 for(let i=0;i<100;i++){requireRunning(server);try{if((await fetch('http://127.0.0.1:8893/')).ok)break;}catch{}await new Promise(r=>setTimeout(r,50));}
 browser=await (process.env.TAU_WORKER_ENGINE==='webkit'?webkit:chromium).launch();
 const context=await browser.newContext();const page=await context.newPage();
 // No application bootstrap: isolate native worker/cache behavior.
 await page.route('http://127.0.0.1:8893/',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><title>Tau cache migration</title>'}));
 await page.goto('http://127.0.0.1:8893/');
 const result=await page.evaluate(async()=>{
  const old=await caches.open('tau-web-shell-v12');await old.put('/old-shell',new Response('old'));
  const unrelated=await caches.open('other-app-cache');await unrelated.put('/other',new Response('keep'));
  const registration=await navigator.serviceWorker.register('/static/retire-sw.js',{scope:'/static/'});
  const deadline=Date.now()+8000;
  while(((await caches.keys()).includes('tau-web-shell-v12') || (await navigator.serviceWorker.getRegistrations()).length) && Date.now()<deadline)await new Promise(r=>setTimeout(r,25));
  return {caches:await caches.keys(),registrations:(await navigator.serviceWorker.getRegistrations()).length,other:await (await caches.match('/other')).text()};
 });
 expect(result.caches).toEqual(['other-app-cache']);expect(result.registrations).toBe(0);expect(result.other).toBe('keep');
 console.log('PASS native worker cache retirement and unrelated-cache preservation');
}finally{await browser?.close();await stopChild(server);}
