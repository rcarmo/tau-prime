import {html,useEffect,useRef,useState} from '../vendor/preact-htm.js';
import {getTauApprovals,resolveTauApproval} from '../api.js';
export function TauApprovals({sessionId}) {
 const [items,setItems]=useState([]);const [error,setError]=useState('');const [busy,setBusy]=useState(false);
 const alive=useRef(true);const pending=useRef(false);
 useEffect(()=>{
  alive.current=true;let loading=false;let controller=null;
  setItems([]);setError('');
  const refresh=async()=>{
   if(loading||pending.current)return;loading=true;controller=new AbortController();
   try{const result=await getTauApprovals(sessionId,{signal:controller.signal});if(alive.current)setItems(result);}
   catch(e){if(alive.current&&e.name!=='AbortError')setError(e.message);}
   finally{loading=false;controller=null;}
  };
  refresh();const timer=setInterval(refresh,1500);
  return()=>{alive.current=false;clearInterval(timer);controller?.abort();};
 },[sessionId]);
 const decide=async(id,decision)=>{
  if(pending.current)return;pending.current=true;setBusy(true);setError('');
  try{
   await resolveTauApproval(id,decision);
   if(alive.current)setItems(current=>current.filter(item=>item.approval_id!==id));
  }catch(e){if(alive.current)setError(e.message);}
  finally{pending.current=false;if(alive.current)setBusy(false);}
 };
 return html`<section aria-label="Tool approvals" aria-live="polite">
 ${error&&html`<div role="alert">${error}</div>`}
 ${items.map(item=>html`<div key=${item.approval_id} class="post-content">
 <h3>Approval required: ${item.tool_name}</h3><p>${item.description}</p>
 <pre style="white-space:pre-wrap;overflow-wrap:anywhere">${JSON.stringify(item.arguments,null,2)}</pre>
 <button type="button" disabled=${busy} onClick=${()=>decide(item.approval_id,'deny')}>Deny ${item.tool_name}</button>
 <button type="button" disabled=${busy} onClick=${()=>decide(item.approval_id,'allow')}>Allow ${item.tool_name}</button>
 </div>`)}
 </section>`;
}
