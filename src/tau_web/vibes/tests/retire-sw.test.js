import {test,expect} from 'bun:test';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
test('upgrade worker removes only Tau shell caches and relinquishes registration',async()=>{
 const handlers={};const deleted=[];let claimed=false,unregistered=false;
 runInNewContext(readFileSync(new URL('../static/retire-sw.js',import.meta.url),'utf8'),{
  self:{addEventListener:(name,fn)=>handlers[name]=fn,skipWaiting:async()=>{},clients:{claim:async()=>{claimed=true;}},registration:{unregister:async()=>{unregistered=true;}}},
  caches:{keys:async()=>['tau-web-shell-v12','other-app-cache'],delete:async name=>deleted.push(name)},
 });
 let pending;handlers.activate({waitUntil:value=>pending=value});await pending;
 expect(deleted).toEqual(['tau-web-shell-v12']);expect(claimed).toBe(true);expect(unregistered).toBe(true);expect(handlers.fetch).toBeUndefined();
});
