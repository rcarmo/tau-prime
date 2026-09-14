// Build replaces this declaration with an exact public-shell manifest.
const SHELL = {"version":"e14ca3a3d7b609318a50","assets":["/","/static/js/bootstrap.js","/static/dist/app.js?v=1","/static/dist/app.css?v=1","/static/extension-ui.js","/static/frontend-sdk.js","/static/widget-bridge.js","/static/fonts/KaTeX_Size1-Regular.woff2","/static/fonts/KaTeX_Caligraphic-Bold.woff2","/static/fonts/KaTeX_Size4-Regular.woff2","/static/fonts/KaTeX_SansSerif-Italic.woff2","/static/fonts/KaTeX_Fraktur-Regular.woff2","/static/fonts/KaTeX_AMS-Regular.woff2","/static/fonts/KaTeX_Fraktur-Bold.woff2","/static/fonts/KaTeX_Size2-Regular.woff2","/static/fonts/KaTeX_Math-BoldItalic.woff2","/static/fonts/KaTeX_Caligraphic-Regular.woff2","/static/fonts/KaTeX_Size3-Regular.woff2","/static/fonts/KaTeX_Main-BoldItalic.woff2","/static/fonts/KaTeX_Typewriter-Regular.woff2","/static/fonts/KaTeX_SansSerif-Bold.woff2","/static/fonts/KaTeX_Main-Italic.woff2","/static/fonts/KaTeX_Script-Regular.woff2","/static/fonts/KaTeX_Main-Regular.woff2","/static/fonts/KaTeX_SansSerif-Regular.woff2","/static/fonts/KaTeX_Main-Bold.woff2","/static/fonts/KaTeX_Math-Italic.woff2","/static/common/fonts/vendor/firacode-nerd-font-mono-bold.ttf","/static/common/fonts/vendor/firacode-nerd-font.meta.json","/static/common/fonts/vendor/firacode-nerd-font-mono-regular.ttf"]};
const CACHE = `tau-vibes-shell-${SHELL.version}`;
self.addEventListener('install', event => {
 event.waitUntil((async()=>{
  const cache=await caches.open(CACHE);
  try{
   for(const path of SHELL.assets){
    const response=await fetch(new Request(path,{credentials:'omit',cache:'reload'}));
    if(!response.ok)throw new Error(`Shell asset unavailable: ${path}`);
    await cache.put(path,response);
   }
  }catch(error){
   await caches.delete(CACHE);
   throw error;
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
  // A controlled navigation uses the entry document belonging to this bundle.
  // A new worker waits for existing clients to close before replacing the cache.
  if(navigation)return (await cache.match('/'))||fetch(request);
  return (await cache.match(url.pathname+url.search))||fetch(request);
 })());
});
