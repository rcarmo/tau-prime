/** Translate real Tau event payloads to the imported Piclaw status presentation. */
export function tauStatus(event, payload, runId) {
 const base={turn_id:runId};
 if(event==='tau.agent.agent_start')return {...base,type:'thinking',title:'Thinking…'};
 if(event==='tau.agent.tool_execution_start')return {...base,type:'tool_call',title:payload.tool_call?.name||'Tool',detail:JSON.stringify(payload.tool_call?.arguments||{})};
 if(event==='tau.agent.tool_execution_update')return {...base,type:'tool_status',title:'Tool',detail:payload.message||''};
 if(event==='tau.agent.tool_execution_end')return {...base,type:'tool_status',title:payload.result?.name||'Tool',detail:payload.result?.content||''};
 if(event==='tau.agent.error')return {...base,type:'error',title:payload.message||'Tau agent error'};
 return null;
}
