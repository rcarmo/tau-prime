import {html,useEffect,useRef,useState} from '../vendor/preact-htm.js';
import {getTauPlan,saveTauPlan} from '../api.js';
// In-memory session drafts survive closing/reopening without persisting content to disk.
const drafts=new Map();
export function TauPlan({sessionId}) {
 const [state,setState]=useState(()=>drafts.get(sessionId)||{text:'',base:'',revision:null,loaded:false});
 const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 const alive=useRef(true);const pending=useRef(false);
 const update=next=>{drafts.set(sessionId,next);if(alive.current)setState(next);};
 const load=async(force=false)=>{
  if(pending.current)return;
  if(force&&state.text!==state.base&&!window.confirm('Discard unsaved plan changes and reload?'))return;
  pending.current=true;setBusy(true);setError('');
  try{
   const plan=await getTauPlan(sessionId);const cached=drafts.get(sessionId);
   if(!alive.current)return;
   if(!force&&cached&&cached.text!==cached.base)return;
   update({text:plan.markdown||'',base:plan.markdown||'',revision:plan.revision,loaded:true});
  }catch(e){if(alive.current)setError(e.message);}
  finally{pending.current=false;if(alive.current)setBusy(false);}
 };
 useEffect(()=>{alive.current=true;load();return()=>{alive.current=false;};},[]);
 const save=async()=>{
  if(pending.current||!state.loaded)return;pending.current=true;setBusy(true);setError('');
  const submitted=state;
  try{
   const plan=await saveTauPlan(sessionId,submitted.text,submitted.revision);
   update({text:plan.markdown||'',base:plan.markdown||'',revision:plan.revision,loaded:true});
  }catch(e){if(alive.current)setError(e.status===409?'Plan changed on the server. Your draft is retained; Reload to review the latest version.':e.message);}
  finally{pending.current=false;if(alive.current)setBusy(false);}
 };
 return html`<section class="tau-plan" aria-label="Session plan">
 <label>Plan markdown<textarea style="width:100%;box-sizing:border-box;min-height:140px" value=${state.text} disabled=${busy||!state.loaded} onInput=${e=>update({...state,text:e.target.value})}/></label>
 <div>Revision ${state.revision??'none'}${state.text!==state.base?' · Unsaved changes':''}</div>
 ${error&&html`<div role="alert">${error}</div>`}
 <button type="button" disabled=${busy||!state.loaded||state.text===state.base} onClick=${save}>Save plan</button>
 <button type="button" disabled=${busy} onClick=${()=>load(true)}>Reload plan</button>
 </section>`;
}
