/** Translate real Tau event payloads to the imported Piclaw status presentation. */
export function mergeTauStatus(current, next) {
 if (!next) return current;
 if (next.type === 'tool_status' && current?.tool_call_id
  && next.tool_call_id !== current.tool_call_id) return current;
 return next.type === 'tool_status' && current?.tool_call_id === next.tool_call_id
  ? {...current,...next,started_at:current.started_at}
  : next;
}

export function tauStatus(event, payload, runId, now = Date.now()) {
 const base={turn_id:runId};
 if(event==='tau.agent.agent_start')return {...base,type:'thinking',title:'Thinking…'};
 if(event==='tau.agent.tool_execution_start')return {...base,type:'tool_call',title:payload.tool_call?.name||'Tool',detail:JSON.stringify(payload.tool_call?.arguments||{}),tool_call_id:payload.tool_call?.id||null,started_at:payload.started_at||now};
 if(event==='tau.agent.tool_execution_update')return {...base,type:'tool_status',title:payload.name||'Tool',detail:payload.message||'',tool_call_id:payload.tool_call_id||null};
 if(event==='tau.agent.tool_execution_end')return {...base,type:'tool_status',title:payload.result?.name||'Tool',detail:payload.result?.content||'',tool_call_id:payload.result?.tool_call_id||null,completed_at:payload.completed_at||now};
 if(event==='tau.agent.error')return {...base,type:'error',title:payload.message||'Tau agent error'};
 return null;
}
