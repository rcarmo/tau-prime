import {test,expect} from 'bun:test';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
test('offline worker intercepts only public shell requests',()=>{
 const handlers={};
 vm.runInNewContext(readFileSync(new URL('../static/offline-sw.js',import.meta.url),'utf8'),{self:{location:{origin:'https://tau.test'},addEventListener:(name,fn)=>handlers[name]=fn},URL});
 for(const path of ['/api/sessions','/api/media/one/content','/static/unknown.js']){
  let intercepted=false;
  handlers.fetch({request:{method:'GET',url:`https://tau.test${path}`,mode:'cors',headers:new Headers()},respondWith:()=>{intercepted=true;}});
  expect(intercepted).toBe(false);
 }
 let intercepted=false;
 handlers.fetch({request:{method:'GET',url:'https://tau.test/',mode:'navigate',headers:new Headers({Authorization:'Bearer fixture'})},respondWith:()=>{intercepted=true;}});
 expect(intercepted).toBe(false);
});
test('offline installation omits credentials and navigation falls back without caching session URL',async()=>{
 const handlers={},entries=new Map(),requests=[];
 let offline=false;
 // Capture constructor options: Bun's Request currently reports include for omit.
 class LocalRequest {constructor(path,options){this.url=new URL(path,'https://tau.test').href;Object.assign(this,options);}}
 vm.runInNewContext(readFileSync(new URL('../static/offline-sw.js',import.meta.url),'utf8'),{
  self:{location:{origin:'https://tau.test'},addEventListener:(name,fn)=>handlers[name]=fn},URL,Request:LocalRequest,Response,
  caches:{open:async()=>({put:async(path,response)=>entries.set(path,response),match:async path=>entries.get(path)?.clone()})},
  fetch:async request=>{if(offline)throw new Error('Offline');requests.push(request);return new Response('public shell');},
 });
 let installed;handlers.install({waitUntil:promise=>{installed=promise;}});await installed;
 expect(requests.length).toBeGreaterThan(7);
 expect(requests.every(request=>request.credentials==='omit'&&request.cache==='reload')).toBe(true);
 expect([...entries.keys()].some(path=>path.startsWith('/api/'))).toBe(false);
 offline=true;let response;
 handlers.fetch({request:{method:'GET',url:'https://tau.test/?session=private',mode:'navigate',headers:new Headers()},respondWith:promise=>{response=promise;}});
 expect(await (await response).text()).toBe('public shell');
 expect(entries.has('/?session=private')).toBe(false);
});
