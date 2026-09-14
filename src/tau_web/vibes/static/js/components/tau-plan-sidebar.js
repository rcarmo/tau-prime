import {html,useEffect,useRef,useState} from '../vendor/preact-htm.js';
import {getTauPlan,saveTauPlan} from '../api.js';
import {createPlanState,planProgress} from '../tau-plan-state.js';
const plans=createPlanState({read:getTauPlan,write:saveTauPlan});
const stored=(key,fallback)=>{try{return localStorage.getItem(key)||fallback;}catch{return fallback;}};
export function TauPlanSidebar({sessionId}){
 const [open,setOpen]=useState(()=>stored('tau.plan.open','false')==='true');
 const [width,setWidth]=useState(()=>Math.min(620,Math.max(300,Number(stored('tau.plan.width','380'))||380)));
 const [,render]=useState(0),editor=useRef(null),drag=useRef(null);
 const state=plans.get(sessionId),dirty=state.text!==state.base,progress=planProgress(state.text);
 const refresh=()=>render(n=>n+1);
 const operate=async task=>{const pending=task();refresh();await pending;refresh();};
 const load=async()=>{if(dirty&&!confirm('Discard unsaved Plan edits and refresh?'))return;await operate(()=>plans.load(sessionId,{discard:true}));};
 const close=async()=>{if(state.busy)return;if(dirty){let ok=false;await operate(async()=>{ok=await plans.save(sessionId);});if(!ok)return;}setOpen(false);};
 useEffect(()=>{try{localStorage.setItem('tau.plan.open',String(open));}catch{}if(open&&sessionId)void operate(()=>plans.load(sessionId));},[open,sessionId]);
 useEffect(()=>{try{localStorage.setItem('tau.plan.width',String(width));}catch{}},[width]);
 useEffect(()=>{const key=e=>{if(open&&e.key==='Escape'){e.preventDefault();void close();}};window.addEventListener('keydown',key);return()=>window.removeEventListener('keydown',key);},[open,sessionId,dirty,state.busy]);
 return html`<div class=${`plan-sidebar-root${open?' is-open':''}`} style=${`--plan-sidebar-width:${width}px`}>
 <button class="plan-sidebar-toggle" type="button" title=${open?'Close plan sidebar':'Open plan sidebar'} aria-label=${open?'Close plan sidebar':'Open plan sidebar'} aria-expanded=${open} onClick=${()=>open?close():setOpen(true)}><span class="plan-sidebar-toggle-meter" aria-hidden="true"><span class="plan-sidebar-toggle-meter-fill" style=${`height:${progress.percent}%`}></span></span><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3L5 8L10 13"/></svg></button>
 <aside class="plan-sidebar" aria-label="Session plan" aria-hidden=${!open} inert=${!open}>
 <div class="plan-sidebar-resizer" role="separator" aria-label="Resize plan sidebar" tabIndex="0" aria-orientation="vertical" onKeyDown=${e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();setWidth(w=>Math.min(620,Math.max(300,w+(e.key==='ArrowLeft'?20:-20))));}}} onPointerDown=${e=>{drag.current={x:e.clientX,width};e.currentTarget.setPointerCapture(e.pointerId);}} onPointerMove=${e=>{if(drag.current)setWidth(Math.min(620,Math.max(300,drag.current.width+drag.current.x-e.clientX)));}} onPointerUp=${()=>{drag.current=null;}} onPointerCancel=${()=>{drag.current=null;}}></div>
 <div class="plan-sidebar-panel"><div class="plan-sidebar-head"><div class="plan-sidebar-title">Plan</div><div class="plan-sidebar-subtitle">${sessionId||'No session'}${dirty?' • unsaved':''}</div></div>
 <div class="plan-sidebar-body"><div class="plan-sidebar-progress" aria-label="Plan checklist progress"><div class="plan-sidebar-progress-meta"><span class="plan-sidebar-progress-label">${progress.total?`${progress.done}/${progress.total} completed`:'No checklist items'}</span><span>${progress.percent}%</span></div><div class="plan-sidebar-progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow=${progress.percent}><span class="plan-sidebar-progress-fill" style=${`width:${progress.percent}%`}></span></div></div>
 <div class="plan-sidebar-editor"><textarea ref=${editor} aria-label="Plan markdown" value=${state.text} disabled=${!sessionId||state.busy} onInput=${e=>{plans.edit(sessionId,e.target.value);refresh();}}></textarea></div></div>
 <div class="plan-sidebar-footer"><div class="plan-sidebar-status" aria-live="polite">${state.error||(state.busy?'Loading…':dirty?'Unsaved changes.':'Ready.')}</div><div class="plan-sidebar-actions"><button disabled=${!sessionId||state.busy} onClick=${load}>Refresh</button><button disabled=${!sessionId||state.busy} onClick=${()=>{if(confirm('Reset this plan?')){plans.edit(sessionId,'');void operate(()=>plans.save(sessionId));}}}>Reset</button><button disabled=${!dirty||state.busy} onClick=${()=>operate(()=>plans.save(sessionId))}>Save</button></div></div>
 </div></aside></div>`;
}
