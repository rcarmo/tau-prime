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
