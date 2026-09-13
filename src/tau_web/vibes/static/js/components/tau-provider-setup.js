import {html,useEffect,useRef,useState} from '../vendor/preact-htm.js';
import {getTauOnboarding,configureTauProvider} from '../api.js';
export function TauProviderSetup({onClose}) {
 const [provider,setProvider]=useState('');const [model,setModel]=useState('');
 const [credential,setCredential]=useState('');const [error,setError]=useState('');
 const [loading,setLoading]=useState(true);const [busy,setBusy]=useState(false);
 const panel=useRef(null);const pending=useRef(false);
 useEffect(()=>{
  let disposed=false;const previous=document.activeElement;
  panel.current?.querySelector('button')?.focus();
  getTauOnboarding().then(result=>{if(!disposed){setProvider(result.default_provider||'');setModel(result.default_model||'');}})
   .catch(e=>{if(!disposed)setError(e.message);}).finally(()=>{if(!disposed)setLoading(false);});
  return()=>{disposed=true;if(previous?.isConnected)previous.focus();};
 },[]);
 const submit=async event=>{
  event.preventDefault();if(pending.current||loading)return;pending.current=true;setBusy(true);setError('');
  try{await configureTauProvider({provider,model,credential});setCredential('');onClose();}
  catch(e){setError(e.message);pending.current=false;setBusy(false);}
 };
 const keys=event=>{
  if(event.key==='Escape'){event.preventDefault();event.stopPropagation();if(!busy)onClose();}
  if(event.key!=='Tab')return;
  const items=[...panel.current.querySelectorAll('input:not(:disabled),button:not(:disabled)')];
  if(event.shiftKey&&document.activeElement===items[0]){event.preventDefault();items.at(-1)?.focus();}
  if(!event.shiftKey&&document.activeElement===items.at(-1)){event.preventDefault();items[0]?.focus();}
 };
 return html`<div class="rename-branch-overlay" onPointerDown=${e=>{if(e.target===e.currentTarget&&!busy)onClose();}}>
 <form ref=${panel} class="rename-branch-panel" role="dialog" aria-modal="true" aria-labelledby="tau-provider-title" onSubmit=${submit} onKeyDown=${keys}>
 <h2 id="tau-provider-title">Provider setup</h2>
 <label>Provider<input class="rename-branch-input" value=${provider} disabled=${busy||loading} onInput=${e=>setProvider(e.target.value)} /></label>
 <label>Model<input class="rename-branch-input" value=${model} disabled=${busy||loading} onInput=${e=>setModel(e.target.value)} /></label>
 <label>Credential (leave blank to retain)<input type="password" autocomplete="off" class="rename-branch-input" value=${credential} disabled=${busy||loading} onInput=${e=>setCredential(e.target.value)} /></label>
 <p class="rename-branch-help">Uses Tau's provider configuration. Credentials are sent only to Tau and are not stored in browser storage.</p>
 ${error&&html`<div role="alert">${error}</div>`}
 <div class="rename-branch-actions"><button type="submit" disabled=${loading||busy||!provider.trim()||!model.trim()}>${busy?'Saving…':'Save provider'}</button><button type="button" disabled=${busy} onClick=${onClose}>Cancel</button></div>
 </form></div>`;
}
