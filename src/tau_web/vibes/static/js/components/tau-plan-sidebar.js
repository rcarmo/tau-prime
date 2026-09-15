import {html,useEffect,useRef,useState} from '../vendor/preact-htm.js';
import {getTauPlan,saveTauPlan,sendAgentMessage} from '../api.js';
import {TauPlanEditor} from './tau-plan-editor.js';
import {createPlanState,planProgress} from '../tau-plan-state.js';
const plans=createPlanState({read:getTauPlan,write:saveTauPlan});
const stored=(key,fallback)=>{try{return localStorage.getItem(key)||fallback;}catch{return fallback;}};
export function TauPlanSidebar({sessionId}){
 const [open,setOpen]=useState(()=>stored('tau.plan.open','false')==='true');
 const [width,setWidth]=useState(()=>Math.min(620,Math.max(300,Number(stored('tau.plan.width','380'))||380)));
 const [,render]=useState(0),drag=useRef(null);
 const selected=useRef(sessionId),selectionEpoch=useRef(0);
 if(selected.current!==sessionId){selected.current=sessionId;selectionEpoch.current++;}
 const submitting=useRef(false);
 const state=plans.get(sessionId),dirty=state.text!==state.base,progress=planProgress(state.text);
 const refresh=()=>render(n=>n+1);
 const operate=async task=>{const pending=task();refresh();await pending;refresh();};
 const load=async()=>{if(dirty&&!confirm('Discard unsaved Plan edits and refresh?'))return;await operate(()=>plans.load(sessionId,{discard:true}));};
 const submit=async()=>{
  if(submitting.current||state.busy||!state.loaded)return;
  submitting.current=true;
  const epoch=selectionEpoch.current;
  try{
   if(!await plans.save(sessionId)||selectionEpoch.current!==epoch)return;
   const text=state.text.trim();if(!text){state.error='Add a plan before submitting.';return;}
   state.busy=true;refresh();
   await sendAgentMessage('default',`Please work through the current session plan, keeping its checklist up to date as work progresses.\n\n${text}`,null,[],'auto',sessionId);
  }catch(error){state.error=error.message;}
  finally{state.busy=false;submitting.current=false;if(state.remotePending)await plans.remote(sessionId);refresh();}
 };
 const reset=async()=>{
  if(state.busy||!state.loaded||!confirm('Reset this plan?'))return;
  const previous=state.text;
  plans.edit(sessionId,'');const resetEdit=state.edit;
  await operate(async()=>{
   const saved=await plans.save(sessionId);
   if(!saved&&state.edit===resetEdit)plans.edit(sessionId,previous);
  });
 };
 const close=async()=>{if(state.busy)return;const epoch=selectionEpoch.current;if(dirty){let ok=false;await operate(async()=>{ok=await plans.save(sessionId);});if(!ok)return;}if(selectionEpoch.current===epoch)setOpen(false);};
 useEffect(()=>{try{localStorage.setItem('tau.plan.open',String(open));}catch{}if(sessionId)void operate(()=>plans.load(sessionId));},[open,sessionId]);
 useEffect(()=>{
  const changed=e=>{if(e.detail?.session_id===sessionId)void operate(()=>plans.remote(sessionId));};
  window.addEventListener('tau:plan-updated',changed);
  return()=>window.removeEventListener('tau:plan-updated',changed);
 },[sessionId]);
 useEffect(()=>{try{localStorage.setItem('tau.plan.width',String(width));}catch{}},[width]);
 useEffect(()=>{const key=e=>{if(open&&e.key==='Escape'){e.preventDefault();void close();}};window.addEventListener('keydown',key);return()=>window.removeEventListener('keydown',key);},[open,sessionId,dirty,state.busy]);
 return html`<div class=${`plan-sidebar-root${open?' open':''}${progress.total?' has-checklist':''}`} style=${`--plan-sidebar-width:${width}px`}>
 <button class="plan-sidebar-toggle" type="button" title=${open?'Close plan sidebar':'Open plan sidebar'} aria-label=${open?'Close plan sidebar':'Open plan sidebar'} aria-expanded=${open} onClick=${()=>open?close():setOpen(true)}><span class="plan-sidebar-toggle-meter" aria-hidden="true"><span class="plan-sidebar-toggle-meter-fill" style=${`height:${progress.percent}%`}></span></span><svg aria-hidden="true" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="10 3 5 8 10 13"/></svg></button>
 <aside class="plan-sidebar-panel" style=${`width:${width}px`} aria-label="Session plan" aria-hidden=${!open} inert=${!open}>
 <div class="plan-sidebar-resizer" role="separator" aria-label="Resize plan sidebar" tabIndex="0" aria-orientation="vertical" onKeyDown=${e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();setWidth(w=>Math.min(620,Math.max(300,w+(e.key==='ArrowLeft'?20:-20))));}}} onPointerDown=${e=>{drag.current={x:e.clientX,width};e.currentTarget.setPointerCapture(e.pointerId);}} onPointerMove=${e=>{if(drag.current)setWidth(Math.min(620,Math.max(300,drag.current.width+drag.current.x-e.clientX)));}} onPointerUp=${()=>{drag.current=null;}} onPointerCancel=${()=>{drag.current=null;}}></div>
 <header class="plan-sidebar-header"><div class="plan-sidebar-title">Plan</div><div class="plan-sidebar-subtitle">${sessionId||'No session'}${dirty?' • unsaved':''}</div></header>
 <div class="plan-sidebar-progress" aria-label="Plan checklist progress"><div class="plan-sidebar-progress-meta"><span class="plan-sidebar-progress-label">${progress.total?`${progress.done}/${progress.total} items complete`:'No checklist items'}</span><span class="plan-sidebar-progress-percent">${progress.percent}%</span></div><div class="plan-sidebar-progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow=${progress.percent}><div class="plan-sidebar-progress-fill" style=${`width:${progress.percent}%`}></div></div></div>
 ${open&&html`<${TauPlanEditor} key=${sessionId} value=${state.text} disabled=${!sessionId||!state.loaded||state.busy} onChange=${text=>{plans.edit(sessionId,text);refresh();}}/>`}
 <footer class="plan-sidebar-footer"><div class="plan-sidebar-status" aria-live="polite">${state.error||(state.busy?'Loading…':dirty?'Unsaved changes.':state.status)}</div><div class="plan-sidebar-actions"><button disabled=${!sessionId||state.busy} onClick=${load}>Refresh</button><button disabled=${!sessionId||!state.loaded||state.busy} onClick=${reset}>Reset</button><button disabled=${!dirty||state.busy} onClick=${()=>operate(()=>plans.save(sessionId))}>Save</button><button class="plan-sidebar-submit" disabled=${!sessionId||!state.loaded||state.busy} onClick=${submit}>Submit to model</button></div></footer>
 </aside></div>`;
}
