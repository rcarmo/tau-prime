import {createTauClient} from './tau-client.js';
export function installTauWidgetActions({target=document,renderer=window.tauExtensionUI,client=createTauClient({getToken:()=>localStorage.getItem('tau.web.authToken')||''})}={}) {
 const handle=async event=>{
  const detail=event.detail;
  if(!detail||!['frame_id','extension_id','widget_id','request_id','name'].every(key=>typeof detail[key]==='string'&&detail[key].length>0&&detail[key].length<=256))return;
  try{
   const result=await client.extensionRequest(`/api/extensions/widgets/${encodeURIComponent(detail.extension_id)}/${encodeURIComponent(detail.widget_id)}/actions/${encodeURIComponent(detail.name)}`,{method:'POST',body:{payload:detail.payload}});
   renderer?.respondWidget(detail.frame_id,detail.request_id,result);
  }catch(error){renderer?.respondWidget(detail.frame_id,detail.request_id,null,error.message||'Widget action failed');}
 };
 target.addEventListener('tau:widget-action',handle);
 return()=>target.removeEventListener('tau:widget-action',handle);
}
