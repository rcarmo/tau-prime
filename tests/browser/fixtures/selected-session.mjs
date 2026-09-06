import { fixedTime, modelName, providerName } from './visual-state.mjs';

export async function installSelectedSession(page) {
  const id = 'visual-review';
  const session = {session_id:id,workspace_id:'visual-workspace',workspace_root:'/workspace',title:'Review session',agent_name:'review',provider_name:providerName,model:modelName,thinking_level:null,active_leaf_id:null,created_at:fixedTime,updated_at:fixedTime,archived_at:null,metadata:{}};
  const responses = {
    '/api/sessions': {sessions:[session]},
    [`/api/sessions/${id}`]: session,
    [`/api/sessions/${id}/branches`]: {branches:[]},
    [`/api/sessions/${id}/messages`]: {messages:[]},
    [`/api/sessions/${id}/context`]: {session_id:id,model:modelName,message_count:2,compaction_count:0,active_leaf_id:null},
    [`/api/sessions/${id}/plan`]: {session_id:id,revision:1,markdown:''},
    [`/api/sessions/${id}/approvals`]: {approvals:[]},
  };
  await page.addInitScript(id=>localStorage.setItem('tau.web.selectedSessionId',id),id);
  await page.route('**/api/sessions**', route=>{
    const pathname=new URL(route.request().url()).pathname;
    if(route.request().method()==='GET' && Object.hasOwn(responses,pathname)) return route.fulfill({contentType:'application/json',body:JSON.stringify(responses[pathname])});
    return route.fallback();
  });
}
