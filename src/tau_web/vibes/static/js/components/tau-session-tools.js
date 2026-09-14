import {html,useEffect,useRef} from '../vendor/preact-htm.js';
import {TauDashboard} from './tau-dashboard.js';
import {TauBranches} from './tau-branches.js';
import {TauMedia} from './tau-media.js';

// Utilities are intentionally outside the reference conversation/composer flow.
export function TauSessionTools({sessionId,onSelect,onProvider,onClose}) {
 const panel=useRef(null);
 useEffect(()=>{
  const previous=document.activeElement;
  panel.current.showModal();
  return()=>{
   if(previous?.isConnected && previous!==document.body)previous.focus();
   else document.querySelector('[data-testid="session-switcher"]')?.focus();
  };
 },[]);
 return html`<dialog ref=${panel} class="tau-session-tools" aria-labelledby="tau-tools-title" onCancel=${event=>{event.preventDefault();onClose();}}>
  <header><h2 id="tau-tools-title">Session tools</h2><button type="button" onClick=${onClose} aria-label="Close session tools">×</button></header>
  <${TauDashboard} onSelect=${onSelect}/>

  <button type="button" class="compose-queue-btn" onClick=${onProvider}>Provider setup</button>
  ${sessionId&&html`
   <${TauBranches} key=${sessionId} sessionId=${sessionId} onSelected=${onSelect}/>
   <${TauMedia} key=${sessionId} sessionId=${sessionId}/>`}
 </dialog>`;
}
