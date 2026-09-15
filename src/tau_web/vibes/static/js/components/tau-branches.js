import {html,useEffect,useRef,useState} from '../vendor/preact-htm.js';
import {getTauBranches,selectTauBranch} from '../api.js';
export function TauBranches({sessionId,onSelected}) {
 const [branches,setBranches]=useState([]);const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 const alive=useRef(true);const pending=useRef(false);
 const refresh=async()=>{try{const result=await getTauBranches(sessionId);if(alive.current)setBranches(result);}catch(e){if(alive.current)setError(e.message);}};
 useEffect(()=>{alive.current=true;refresh();return()=>{alive.current=false;};},[]);
 const select=async leaf=>{
  if(pending.current||!window.confirm('Switch conversation branch? The active conversation context will change.'))return;
  pending.current=true;setBusy(true);setError('');
  try{await selectTauBranch(sessionId,leaf);if(alive.current){await refresh();await onSelected?.(sessionId);}}
  catch(e){if(alive.current)setError(e.message);}
  finally{pending.current=false;if(alive.current)setBusy(false);}
 };
 return html`<details><summary>Conversation branches</summary><section aria-label="Conversation branches">
 <button type="button" disabled=${busy} onClick=${refresh}>Refresh branches</button>
 ${error&&html`<div role="alert">${error}</div>`}
 ${branches.length===0&&html`<p>No conversation branches yet.</p>`}
 ${branches.map(branch=>html`<button type="button" key=${branch.leaf_entry_id} disabled=${busy||branch.active} aria-pressed=${branch.active} onClick=${()=>select(branch.leaf_entry_id)}>Leaf ${branch.leaf_entry_id} · depth ${branch.depth}${branch.active?' (active)':''}</button>`)}
 </section></details>`;
}
