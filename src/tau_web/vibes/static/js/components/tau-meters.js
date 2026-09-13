import {html,useEffect,useState} from '../vendor/preact-htm.js';
import {getTauMeters} from '../api.js';
const percent=value=>typeof value==='number'&&Number.isFinite(value)?`${value.toFixed(1)}%`:'Unavailable';
export function TauMeters(){
 const [open,setOpen]=useState(false),[snapshot,setSnapshot]=useState(null),[error,setError]=useState('');
 useEffect(()=>{
  if(!open)return;let disposed=false,loading=false;
  const refresh=async()=>{if(loading)return;loading=true;try{const result=await getTauMeters();if(!disposed){setSnapshot(result);setError('');}}catch(e){if(!disposed)setError(e.message);}finally{loading=false;}};
  refresh();const timer=setInterval(refresh,2000);return()=>{disposed=true;clearInterval(timer);};
 },[open]);
 return html`<details onToggle=${e=>setOpen(e.currentTarget.open)}><summary>Runtime metrics</summary><section aria-label="Runtime metrics">
 ${error&&html`<div role="alert">${error}</div>`}
 ${snapshot?html`<dl><dt>Host CPU</dt><dd>${percent(snapshot.cpu_percent)}</dd><dt>Host RAM</dt><dd>${percent(snapshot.ram_percent)}</dd><dt>Host swap</dt><dd>${percent(snapshot.swap_percent)}</dd><dt>Tau process RSS</dt><dd>${typeof snapshot.process_rss_bytes==='number'?`${(snapshot.process_rss_bytes/1048576).toFixed(1)} MiB`:'Unavailable'}</dd></dl>`:html`<p>Waiting for metrics…</p>`}
 </section></details>`;
}
