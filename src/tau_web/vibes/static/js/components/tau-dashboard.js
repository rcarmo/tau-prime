import {html,useEffect,useRef,useState} from '../vendor/preact-htm.js';
import {getTauDashboard} from '../api.js';
export function TauDashboard({onSelect}){
 const [open,setOpen]=useState(false),[page,setPage]=useState(1),[data,setData]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const panel=useRef(null);
 useEffect(()=>{
  if(!open)return;let disposed=false,loading=false;setData(null);
  const refresh=async()=>{if(loading)return;loading=true;try{const result=await getTauDashboard(page);if(!disposed){setData(result);setError('');}}catch(e){if(!disposed)setError(e.message);}finally{loading=false;}};
  refresh();const timer=setInterval(refresh,3000);return()=>{disposed=true;clearInterval(timer);};
 },[open,page]);
 const select=async id=>{
  if(busy||!window.confirm('Open this session? Unsaved session drafts will be retained.'))return;
  setBusy(true);setError('');try{await onSelect(id);if(panel.current)panel.current.open=false;}catch(e){setError(e.message);}finally{setBusy(false);}
 };
 return html`<details ref=${panel} onToggle=${e=>setOpen(e.currentTarget.open)}><summary>Session dashboard</summary><section aria-label="Session dashboard">
 ${error&&html`<div role="alert">${error}</div>`}
 ${data?html`<p>${data.total_sessions} sessions · ${data.active_sessions} active</p>${data.sessions.map(session=>html`<article key=${session.session_id}>
 <button type="button" disabled=${busy} onClick=${()=>select(session.session_id)}>Open ${session.title||session.session_id}</button>
 <p>${session.activity} · ${session.model||'Model unavailable'} · ${session.queue_count} queued</p>
 <p>${session.summary||''}</p><pre style="white-space:pre-wrap;overflow-wrap:anywhere">${session.preview_text||''}</pre>
 </article>`)}
 <button type="button" disabled=${page<=1||busy} onClick=${()=>setPage(p=>p-1)}>Previous page</button><span>Page ${data.page} of ${data.total_pages}</span><button type="button" disabled=${page>=data.total_pages||busy} onClick=${()=>setPage(p=>p+1)}>Next page</button>`:html`<p>Loading dashboard…</p>`}
 </section></details>`;
}
