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
