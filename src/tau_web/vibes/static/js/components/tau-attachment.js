import {html,useEffect,useRef,useState} from '../vendor/preact-htm.js';
import {getTauMediaBlob} from '../api.js';
export function TauAttachment({attachment}) {
 const [url,setUrl]=useState(null);const [error,setError]=useState('');const [busy,setBusy]=useState(false);
 const alive=useRef(true);const objectUrl=useRef(null);
 const image=['image/png','image/jpeg','image/gif','image/webp','image/avif'].includes(attachment.media_type);
 const load=async()=>{
  setBusy(true);setError('');
  try{
   const blob=await getTauMediaBlob(attachment.media_id);if(!alive.current)return null;
   if(objectUrl.current)URL.revokeObjectURL(objectUrl.current);
   objectUrl.current=URL.createObjectURL(blob);setUrl(objectUrl.current);return objectUrl.current;
  }catch(e){if(alive.current)setError(e.message);return null;}
  finally{if(alive.current)setBusy(false);}
 };
 useEffect(()=>{alive.current=true;if(image)load();return()=>{alive.current=false;if(objectUrl.current)URL.revokeObjectURL(objectUrl.current);};},[]);
 const download=async()=>{
  const href=url||await load();if(!href||!alive.current)return;
  const link=document.createElement('a');link.href=href;link.download=attachment.filename||'attachment';document.body.append(link);link.click();link.remove();
 };
 return html`<div class="tau-attachment">
 ${image&&url&&html`<img src=${url} alt=${attachment.filename||'Attached image'} style="max-width:100%;max-height:400px;object-fit:contain"/>`}
 <button type="button" disabled=${busy} onClick=${download}>Download ${attachment.filename||'attachment'}</button>
 ${error&&html`<span role="alert">${error}</span>`}
 </div>`;
}
