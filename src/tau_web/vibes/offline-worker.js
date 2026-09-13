// Build replaces this declaration with an exact public-shell manifest.
const SHELL = __TAU_SHELL__;
const CACHE = `tau-vibes-shell-${SHELL.version}`;
self.addEventListener('install', event => {
 event.waitUntil((async()=>{
  const cache=await caches.open(CACHE);
  for(const path of SHELL.assets){
   const response=await fetch(new Request(path,{credentials:'omit',cache:'reload'}));
   if(!response.ok)throw new Error(`Shell asset unavailable: ${path}`);
   await cache.put(path,response);
  }
 })());
});
// No skipWaiting: an active page must not acquire a different bundle mid-session.
self.addEventListener('activate',event=>{
 event.waitUntil((async()=>{
  for(const key of await caches.keys())if((key.startsWith('tau-vibes-shell-')||key.startsWith('tau-web-shell-'))&&key!==CACHE)await caches.delete(key);
  await self.clients.claim();
 })());
});
self.addEventListener('fetch',event=>{
 const request=event.request,url=new URL(request.url);
 if(request.method!=='GET'||url.origin!==self.location.origin||request.headers.has('Authorization'))return;
 const navigation=request.mode==='navigate'&&url.pathname==='/';
 const asset=SHELL.assets.includes(url.pathname+url.search);
 if(!navigation&&!asset)return;
 event.respondWith((async()=>{
  const cache=await caches.open(CACHE);
  if(navigation){
   try{return await fetch(request);}catch{
    return (await cache.match('/'))||Response.error();
   }
  }
  return (await cache.match(url.pathname+url.search))||fetch(request);
 })());
});
