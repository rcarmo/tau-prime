/** Session-local Plan state. Never apply a late response over a newer edit. */
export function planProgress(markdown) {
 const matches=String(markdown||'').matchAll(/^\s*(?:[-*+]|\d+[.)])\s+\[([ xX-])\]\s+\S/gm);
 let total=0,done=0;
 for(const match of matches){total++;if(match[1].toLowerCase()==='x')done++;}
 return {total,done,percent:total?Math.round(done*100/total):0};
}
export function createPlanState({read,write}) {
 const sessions=new Map();
 const get=id=>{
  if(!sessions.has(id))sessions.set(id,{text:'',base:'',revision:null,loaded:false,busy:false,remotePending:false,error:'',edit:0,epoch:0});
  return sessions.get(id);
 };
 const reconcile=async id=>{
  const state=get(id);
  if(!state.remotePending||state.busy)return false;
  state.remotePending=false;
  if(state.text!==state.base){state.error='Plan changed remotely; your draft is retained. Refresh to reconcile.';return false;}
  return api.load(id);
 };
 const api = {
  get,
  async remote(id){if(!id)return false;get(id).remotePending=true;return reconcile(id);},
  edit(id,text){const state=get(id);state.text=text;state.edit++;},
  async load(id,{discard=false}={}){
   if(!id)throw new Error('Select a session first');
   const state=get(id);
   if(state.busy)return false;
   if(!discard&&state.loaded&&state.text!==state.base)return false;
   const epoch=++state.epoch,edit=state.edit;
   state.busy=true;state.error='';
   try{
    const result=await read(id);
    if(epoch!==state.epoch)return false;
    if(edit!==state.edit){state.error='Plan changed while loading; your edits were retained.';return false;}
    state.text=result.markdown;state.base=result.markdown;state.revision=result.revision;state.loaded=true;
    return true;
   }catch(error){if(epoch===state.epoch)state.error=error.message;return false;}
   finally{if(epoch===state.epoch){state.busy=false;await reconcile(id);}}
  },
  async save(id){
   const state=get(id);if(!id||state.busy||!state.loaded)return false;
   if(state.text===state.base)return true;
   const text=state.text,edit=state.edit,epoch=++state.epoch;
   state.busy=true;state.error='';
   try{
    const result=await write(id,text,state.revision);
    if(epoch!==state.epoch)return false;
    state.base=result.markdown;state.revision=result.revision;
    if(edit===state.edit)state.text=result.markdown;
    return state.text===state.base;
   }catch(error){state.error=error.status===409?'Plan changed remotely. Refresh to reconcile; your draft is retained.':error.message;return false;}
   finally{if(epoch===state.epoch){state.busy=false;await reconcile(id);}}
  },
 };
 return api;
}
