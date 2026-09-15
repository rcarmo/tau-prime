import {html,useEffect,useRef,useState} from '../vendor/preact-htm.js';
import {getTauMedia,getTauMediaBlob} from '../api.js';
export function TauMedia({sessionId}) {
 const [items,setItems]=useState([]);const [error,setError]=useState('');const [busy,setBusy]=useState(false);
 const alive=useRef(true);const pending=useRef(false);const urls=useRef(new Set());
 const refresh=async()=>{try{const media=await getTauMedia(sessionId);if(alive.current){setItems(media);setError('');}}catch(e){if(alive.current)setError(e.message);}};
 useEffect(()=>{alive.current=true;refresh();return()=>{alive.current=false;for(const url of urls.current)URL.revokeObjectURL(url);urls.current.clear();};},[]);
 const download=async item=>{
  if(pending.current)return;pending.current=true;setBusy(true);setError('');
  try{
   const blob=await getTauMediaBlob(item.media_id);if(!alive.current)return;
   const url=URL.createObjectURL(blob);urls.current.add(url);
   const link=document.createElement('a');link.href=url;link.download=item.filename||'attachment';document.body.append(link);link.click();link.remove();
   setTimeout(()=>{URL.revokeObjectURL(url);urls.current.delete(url);},30000);
  }catch(e){if(alive.current)setError(e.message);}
  finally{pending.current=false;if(alive.current)setBusy(false);}
 };
 return html`<details><summary>Session media</summary><section aria-label="Session media">
 <button type="button" onClick=${refresh}>Refresh media</button>
 ${error&&html`<div role="alert">${error}</div>`}
 ${items.map(item=>html`<div key=${item.media_id}><button type="button" disabled=${busy} onClick=${()=>download(item)}>Download ${item.filename}</button></div>`)}
 </section></details>`;
}
