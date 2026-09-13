import {createTauClient} from './tau-client.js';
export async function activateTauExtensions({getSessionId,navigate,fetchImpl=globalThis.fetch,sdk=globalThis.tauFrontendSDK,getToken=()=>localStorage.getItem('tau.web.authToken')||''}) {
 const client=createTauClient({fetchImpl,getToken});
 const modules=await client.frontendModules();
 sdk.configure({
  fetchAsset:path=>{
   const url=new URL(path,location.origin);
   if(url.origin!==location.origin||!url.pathname.startsWith('/api/extensions/assets/'))throw new Error('Invalid extension asset URL');
   const token=getToken();return fetchImpl(url.pathname+url.search,{headers:token?{Authorization:`Bearer ${token}`}:{},credentials:'same-origin'});
  },
  request:(path,options={})=>client.extensionRequest(path,{...options,body:typeof options.body==='string'?JSON.parse(options.body):options.body}),
  submit:payload=>{
   if(!payload||typeof payload.text!=='string'||!payload.text.trim()||payload.text.length>16384||Object.keys(payload).some(k=>!['text','mode'].includes(k)))throw new Error('Invalid extension submission');
   const mode=payload.mode||'run';
   if(!['run','steer','follow_up'].includes(mode))throw new Error('Invalid extension delivery mode');
   return client.send(getSessionId(),payload.text,{mode});
  },
  navigate:async id=>{
   if(typeof id!=='string'||!id||id.length>256)throw new Error('Invalid session target');
   const {sessions}=await client.sessions();
   if(!sessions.some(s=>s.id===id))throw new Error('Unknown session target');
   await navigate(id);return {session_id:id};
  },
 });
 return sdk.loadAll(modules);
}
