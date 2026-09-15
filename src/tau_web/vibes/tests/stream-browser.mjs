import {createServer} from 'node:http';
import {spawn} from 'node:child_process';
import {chromium,webkit,expect} from '@playwright/test';
import {requireFreePorts,stopChild} from './server-lifecycle.mjs';
await requireFreePorts(8893,8894);
let connections=0;const cursors=[];const timers=new Set();
const later=(fn,delay)=>{const timer=setTimeout(()=>{timers.delete(timer);fn();},delay);timers.add(timer);};
const backend=createServer((req,res)=>{
 if(req.url!=='/api/events'){res.writeHead(404).end();return;}
 if(req.headers.authorization!=='Bearer stream-fixture'){res.writeHead(401).end();return;}
 connections++;cursors.push(req.headers['last-event-id']||null);
 res.writeHead(200,{'Content-Type':'text/event-stream','Cache-Control':'no-cache'});res.flushHeaders();
 const frame=(id,eventId,text)=>`id: ${id}\nevent: tau.agent.message_delta\ndata: ${JSON.stringify({event_id:eventId,session_id:'one',run_id:'run',payload:{delta:text}})}\n\n`;
 if(connections===1){
  const bytes=Buffer.from(frame(1,'first','日本'));
  const split=bytes.indexOf(Buffer.from('日本'))+1;
  res.write(bytes.subarray(0,split));
  later(()=>res.write(bytes.subarray(split)),75);
  later(()=>res.end(),150);
 }else{
  res.write(frame(1,'first','日本')); // replay must not append twice
  later(()=>res.write(frame(2,'second',' recovered')),75);
 }
 req.on('error',()=>{});
});
await new Promise(resolve=>backend.listen(8894,'127.0.0.1',resolve));
const proxy=spawn('bun',['dev-server.js'],{cwd:new URL('..',import.meta.url),env:{...process.env,TAU_VIBES_PORT:'8893',TAU_VIBES_BACKEND:'http://127.0.0.1:8894'},stdio:'ignore'});
let browser;
try{
 for(let i=0;i<100;i++){try{if((await fetch('http://127.0.0.1:8893/')).ok)break;}catch{}await new Promise(r=>setTimeout(r,50));}
 browser=await (process.env.TAU_STREAM_ENGINE==='webkit'?webkit:chromium).launch();
 const page=await browser.newPage();
 // Same-origin blank document, deliberately no app requests or buffering mocks.
 await page.route('http://127.0.0.1:8893/',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><title>Stream transport test</title>'}));
 await page.goto('http://127.0.0.1:8893/');
 const result=await page.evaluate(async()=>{
  const {TauEventStream}=await import('/static/js/tau-events.js');
  const frames=[],statuses=[];
  const stream=new TauEventStream({getToken:()=> 'stream-fixture',retryMs:50,onFrame:f=>frames.push(f),onStatus:s=>statuses.push(s)});
  try{
   stream.connect();const deadline=Date.now()+8000;
   while(frames.length<2&&Date.now()<deadline)await new Promise(r=>setTimeout(r,20));
   stream.reconnectIfNeeded();
   return {text:frames.map(f=>f.data.payload.delta).join(''),cursor:stream.cursor,statuses,error:String(stream.lastError)};
  }finally{stream.disconnect();}
 });
 console.log(result,connections,cursors);
 expect(result.text).toBe('日本 recovered');expect(result.cursor).toBe('2');
 expect(result.statuses).toContain('disconnected');expect(cursors).toEqual([null,'1']);
 console.log('PASS sustained authenticated browser SSE: split UTF-8, reconnect cursor, replay dedupe');
}finally{
 await browser?.close();await stopChild(proxy);
 for(const timer of timers)clearTimeout(timer);
 backend.closeAllConnections();await new Promise(resolve=>backend.close(resolve));
}
