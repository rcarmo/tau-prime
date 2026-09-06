import { piclawPosts, fixedTime } from '../fixtures/visual-state.mjs';
import { createRequire } from 'node:module';
import { expect, test } from '@playwright/test';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
const frontendRequire = createRequire(path.resolve(import.meta.dirname,'../../../src/tau_web/frontend/package.json'));
const markedModule = frontendRequire.resolve('marked');
const dist = '/opt/piclaw/releases/piclaw-2.15.3-linux-x64-baseline/app/runtime/web/static/visual/dist';

test('capture actual Piclaw application bundle with isolated backend fixture', async ({ page }, info) => {
  const requests = [], errors = [], unexpected = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('http://piclaw-reference.test/**', async route => {
    const url = new URL(route.request().url()); requests.push(url.pathname);
    if(url.pathname === '/') return route.fulfill({contentType:'text/html',body:'<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="/assets/app.bundle.css"><div id="app"></div><script type="module">import {marked} from "/fixture-marked.js"; window.marked=marked; await import("/assets/app.bundle.js");</script>'});
    if(url.pathname.startsWith('/assets/')) {
      const filename=path.basename(url.pathname);
      try { return route.fulfill({body:await readFile(path.join(dist,filename)),contentType:filename.endsWith('.js')?'application/javascript':filename.endsWith('.css')?'text/css':filename.endsWith('.woff2')?'font/woff2':'font/ttf'}); } catch { return route.fulfill({status:404,body:''}); }
    }
    if(url.pathname === '/fixture-marked.js') return route.fulfill({contentType:'application/javascript',body:await readFile(markedModule)});
    const json = data => route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
    if(url.pathname === '/timeline') return json({posts:[...piclawPosts].reverse(),has_more:false});
    if(url.pathname === '/agent/system-metrics') return json({cpu_percent:10,ram_percent:25,swap_percent:0,buffer_cache_bytes:1048576,vram_percent:null,gpu_provider:null,process_memory:{rss_bytes:83886080}});
    if(url.pathname === '/workspace/tree') return json({root:{name:'workspace',path:'',type:'directory',children:[]}});
    if(url.pathname === '/agent/addons/web-entries') return json({entries:[]});
    if(url.pathname === '/agent/active-chats') return json({chats:[]});
    if(url.pathname === '/agent/status') return json(null);
    if(url.pathname === '/agent/context') return json({tokens:null});
    if(url.pathname === '/agent/roster') return json({agents:[]});
    if(url.pathname === '/static/icon-192.png') return route.fulfill({contentType:'image/png',body:await readFile(path.resolve(dist,'../../icon-192.png'))});
    if(url.pathname.startsWith('/avatar/')) return route.fulfill({status:404,body:''});
    if(url.pathname === '/agent/models') return json({models:[],oobe:{provider_ready_completed_instance:true}});
    if(url.pathname === '/agent/branches') return json({chats:[]});
    if(url.pathname.includes('events') || url.pathname === '/sse/stream') return route.fulfill({contentType:'text/event-stream',body:': fixture\n\n'});
    unexpected.push(url.pathname);
    return route.fulfill({status:501,body:'Unmapped reference fixture endpoint'});
  });
  await page.addInitScript(() => localStorage.setItem('piclaw-sidebar-collapsed','true'));
  await page.clock.setFixedTime(new Date(fixedTime));
  await page.goto('http://piclaw-reference.test/',{waitUntil:'domcontentloaded'});
  await expect(page.locator('.app-layout')).toBeVisible();
  await expect(page.locator('.message-list__item--user .message-list__content')).toContainText('Review the workspace');
  await expect(page.locator('.message-list__content h2')).toHaveText('Workspace review');
  await page.locator('.message-list__tool-call-header').click();
  await expect(page.locator('.message-list__tool-call-body')).toBeVisible();
  await page.evaluate(()=>document.fonts.ready);
  const geometry = await page.locator('.activity-bar, .app-layout__sidebar-wrapper, .tab-bar, .chat__compose, .chat__compose-container, .chat__input, .chat__toolbar, .chat__send-btn, .app-layout__status-bar').evaluateAll(elements => elements.map(el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return {fontSize:s.fontSize,fontFamily:s.fontFamily,verticalAlign:s.verticalAlign,whiteSpace:s.whiteSpace,padding:s.padding,margin:s.margin,display:s.display,gap:s.gap,lineHeight:s.lineHeight,className:el.className,x:r.x,y:r.y,width:r.width,height:r.height};}));
  await mkdir('/workspace/tmp/piclaw-full-reference',{recursive:true});
  await page.screenshot({path:`/workspace/tmp/piclaw-full-reference/${info.project.name}.png`});
  await writeFile(`/workspace/tmp/piclaw-full-reference/${info.project.name}.json`,JSON.stringify({requests:[...new Set(requests)],errors,unexpected,geometry},null,2));
  expect(errors).toEqual([]);
  expect(unexpected).toEqual([]);
});
