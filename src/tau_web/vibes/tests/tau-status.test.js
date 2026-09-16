import {test,expect} from 'bun:test';
import {mergeTauStatus,tauStatus} from '../static/js/tau-status.js';
test('Tau tool and error payloads preserve call identity and timing',()=>{
 expect(tauStatus('tau.agent.tool_execution_start',{tool_call:{id:'call-1',name:'read',arguments:{path:'README.md'}}},'r',1000)).toEqual({turn_id:'r',type:'tool_call',title:'read',detail:'{"path":"README.md"}',tool_call_id:'call-1',started_at:1000});
 expect(tauStatus('tau.agent.tool_execution_update',{tool_call_id:'call-1',name:'read',message:'Reading…'},'r',1500)).toEqual({turn_id:'r',type:'tool_status',title:'read',detail:'Reading…',tool_call_id:'call-1'});
 expect(tauStatus('tau.agent.tool_execution_end',{result:{tool_call_id:'call-1',name:'read',content:'Done'}},'r',2500)).toEqual({turn_id:'r',type:'tool_status',title:'read',detail:'Done',tool_call_id:'call-1',completed_at:2500});
 expect(tauStatus('tau.agent.error',{message:'Failure'},'r').title).toBe('Failure');
 expect(tauStatus('tau.agent.message_delta',{delta:'text'},'r')).toBe(null);
});
test('same-named tool updates remain routed by call identity',()=>{
 const current={type:'tool_call',title:'read',tool_call_id:'call-1',started_at:1000};
 expect(mergeTauStatus(current,{type:'tool_status',title:'read',tool_call_id:'call-2',detail:'wrong'})).toBe(current);
 expect(mergeTauStatus(current,{type:'tool_status',title:'read',tool_call_id:'call-1',detail:'right'})).toEqual({...current,type:'tool_status',detail:'right'});
});
