import {html,useEffect,useState} from '../vendor/preact-htm.js';
import {getTauMeters} from '../api.js';
import {meterRows} from '../tau-meter-data.js';
const initialCollapsed=()=>{try{return localStorage.getItem('tau.meters.collapsed')==='true';}catch{return false;}};
export function TauMeters(){
 const [compact,setCompact]=useState(()=>window.matchMedia('(max-width: 600px)').matches);
 useEffect(()=>{const media=window.matchMedia('(max-width: 600px)');const change=()=>setCompact(media.matches);media.addEventListener('change',change);return()=>media.removeEventListener('change',change);},[]);
 const [collapsed,setCollapsed]=useState(initialCollapsed),[snapshot,setSnapshot]=useState(null),[error,setError]=useState('');
 useEffect(()=>{try{localStorage.setItem('tau.meters.collapsed',String(collapsed));}catch{}},[collapsed]);
 useEffect(()=>{
  if(collapsed)return;let disposed=false,loading=false;
  const refresh=async()=>{
   if(loading||document.hidden)return;loading=true;
   try{const result=await getTauMeters();if(!disposed){setSnapshot(result);setError('');}}
   catch(e){if(!disposed){setSnapshot(null);setError(e.message);}}
   finally{loading=false;}
  };
  void refresh();const timer=setInterval(refresh,2000);
  document.addEventListener('visibilitychange',refresh);
  return()=>{disposed=true;clearInterval(timer);document.removeEventListener('visibilitychange',refresh);};
 },[collapsed]);
 const rows=meterRows(snapshot||{});
 const summary=rows.filter(row=>row.kind==='cpu'||row.kind==='ram'||(row.kind==='swap'&&snapshot?.swap_percent>0)).map(row=>`${row.label.toUpperCase()} ${row.value}`).join(' • ');
 return html`<div class=${`system-meters-hud system-meters-hud-overlay${collapsed?' is-collapsed':''}`}>
 <button type="button" class="system-meters-card" aria-label=${collapsed?'Expand system meters':'Collapse system meters'} aria-expanded=${!collapsed} title=${error?`Metrics unavailable: ${error}`:'Host CPU, memory, swap and Tau process RSS'} onClick=${()=>setCollapsed(value=>!value)}>
 ${collapsed?html`<span class="system-meters-collapse-tab" aria-hidden="true">‹</span>`:compact?html`<span class="system-meters-compact-summary">${summary}</span>`:rows.map(row=>html`<span class=${`system-meters-row ${row.kind}`} key=${row.kind}><span class="system-meters-label">${row.label}</span><svg class="system-meters-spark" viewBox="0 0 56 16" aria-hidden="true"><path d=${row.path}/></svg><span class="system-meters-value">${row.value}</span></span>`)}
 </button></div>`;
}
