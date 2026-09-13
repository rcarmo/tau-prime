import {createTauClient} from './tau-client.js';
export function installTauWidgetActions({target=document,renderer=window.tauExtensionUI,client=createTauClient({getToken:()=>localStorage.getItem('tau.web.authToken')||''}),onError=console.error}={}) {
 const handle=async event=>{
  const detail=event.detail;
  if(!detail||!['frame_id','extension_id','widget_id','request_id','name'].every(key=>typeof detail[key]==='string'&&detail[key].length>0&&detail[key].length<=256))return;
  try{
   const result=await client.extensionRequest(`/api/extensions/widgets/${encodeURIComponent(detail.extension_id)}/${encodeURIComponent(detail.widget_id)}/actions/${encodeURIComponent(detail.name)}`,{method:'POST',body:{payload:detail.payload}});
   if(!disposed)renderer?.respondWidget(detail.frame_id,detail.request_id,{result});
  }catch(error){if(!disposed)renderer?.respondWidget(detail.frame_id,detail.request_id,{error:error.message||'Widget action failed'});}
 };
 let disposed=false;const refreshes=new Map();
 const refresh=async event=>{
  const detail=event.detail;if(!detail||typeof detail.frame_id!=='string')return;
  const generation=(refreshes.get(detail.frame_id)||0)+1;refreshes.set(detail.frame_id,generation);
  try{
   const text=await client.widgetDocument(detail.extension_id,detail.widget_id);
   if(!disposed&&refreshes.get(detail.frame_id)===generation)renderer?.refreshWidget(detail.frame_id,text);
  }catch(error){if(!disposed&&refreshes.get(detail.frame_id)===generation)onError(error);}
 };
 target.addEventListener('tau:widget-action',handle);
 target.addEventListener('tau:widget-refresh',refresh);
 return()=>{disposed=true;target.removeEventListener('tau:widget-action',handle);target.removeEventListener('tau:widget-refresh',refresh);};
}
