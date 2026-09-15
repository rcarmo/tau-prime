import {test,expect} from 'bun:test';
import {consumeTauEvents,TauEventStream} from '../static/js/tau-events.js';
test('SSE handles fragmented UTF-8, CRLF, comments and multiple frames',async()=>{
 const bytes=new TextEncoder().encode(': ping\r\nid: 7\r\nevent: tau.snapshot\r\ndata: {"text":"日本"}\r\n\r\nid: 8\ndata: {"ok":true}\n\n');
 const frames=[];
 const body=new ReadableStream({start(c){for(const byte of bytes)c.enqueue(new Uint8Array([byte]));c.close();}});
 await consumeTauEvents(body,f=>frames.push(f));
 expect(frames).toEqual([{event:'tau.snapshot',id:'7',data:{text:'日本'}},{event:'message',id:'8',data:{ok:true}}]);
});
test('reconnect forwards auth and committed cursor; disconnect stops retries',async()=>{
 const calls=[];const frames=[];
 const stream=new TauEventStream({retryMs:5,getToken:()=> 'fixture',onFrame:f=>frames.push(f),fetchImpl:async(path,options)=>{
  calls.push({path,options});
  return new Response('id: 42\nevent: tau.snapshot\ndata: {}\n\n',{headers:{'Content-Type':'text/event-stream'}});
 }});
 try {stream.connect(); for(let i=0;i<100 && calls.length<2;i++)await Bun.sleep(5);
 expect(calls.length).toBeGreaterThanOrEqual(2);
 expect(calls[0].options.headers.Authorization).toBe('Bearer fixture');
 expect(calls[1].options.headers['Last-Event-ID']).toBe('42');
 }finally{stream.disconnect();}
 const count=calls.length;await Bun.sleep(20);expect(calls.length).toBe(count);
});
test('replayed event ids are delivered once while cursor advances',async()=>{
 const frames=[];let stream;
 stream=new TauEventStream({retryMs:10000,onFrame:f=>frames.push(f),fetchImpl:async()=>new Response(
 'id: 1\nevent: tau.agent.message_delta\ndata: {"event_id":"same","payload":{"delta":"x"}}\n\nid: 2\nevent: tau.agent.message_delta\ndata: {"event_id":"same","payload":{"delta":"x"}}\n\n',
 {headers:{'Content-Type':'text/event-stream'}})});
 try { stream.connect(); for(let i=0;i<100 && stream.cursor!=='2';i++)await Bun.sleep(2);
 expect(frames.length).toBe(1);expect(stream.cursor).toBe('2');
 }finally{stream.disconnect();}
});
test('focus preserves a healthy stream and reconnects after disconnect',async()=>{
 let calls=0,cancelled=0;
 const stream=new TauEventStream({onFrame:()=>{},fetchImpl:async()=>{
  calls++;return new Response(new ReadableStream({cancel(){cancelled++;}}),{headers:{'Content-Type':'text/event-stream'}});
 }});
 try{
  stream.connect();for(let i=0;i<100&&!stream.connected;i++)await Bun.sleep(2);
  expect(stream.connected).toBe(true);stream.reconnectIfNeeded();await Bun.sleep(5);expect(calls).toBe(1);
  stream.disconnect();await Bun.sleep(5);expect(cancelled).toBe(1);
  stream.reconnectIfNeeded();for(let i=0;i<100&&!stream.connected;i++)await Bun.sleep(2);
  expect(calls).toBe(2);expect(stream.connected).toBe(true);
 }finally{stream.disconnect();}
});
test('failed event consumer leaves cursor and dedupe uncommitted',async()=>{
 const stream=new TauEventStream({retryMs:10000,onFrame:()=>{throw new Error('consumer failed');},fetchImpl:async()=>new Response('id: 9\nevent: tau.test\ndata: {"event_id":"failed"}\n\n',{headers:{'Content-Type':'text/event-stream'}})});
 try{
  stream.connect();for(let i=0;i<100&&!stream.lastError;i++)await Bun.sleep(2);
  expect(stream.lastError.message).toBe('consumer failed');expect(stream.cursor).toBe(null);expect(stream.seenEvents.has('failed')).toBe(false);
 }finally{stream.disconnect();}
});
test('focus storm does not restart pending connection',async()=>{
 let calls=0;let release;
 const stream=new TauEventStream({onFrame:()=>{},fetchImpl:()=>{calls++;return new Promise(resolve=>{release=resolve;});}});
 try{
  stream.connect();for(let i=0;i<10;i++)stream.reconnectIfNeeded();expect(calls).toBe(1);
  release(new Response(new ReadableStream({}),{headers:{'Content-Type':'text/event-stream'}}));
  for(let i=0;i<100&&!stream.connected;i++)await Bun.sleep(2);
  expect(stream.connected).toBe(true);expect(stream.connecting).toBe(false);
 }finally{stream.disconnect();}
});
