import {test,expect} from 'bun:test';
import {tauStatus} from '../static/js/tau-status.js';
test('Tau tool and error payloads map to existing status presentation',()=>{
 expect(tauStatus('tau.agent.tool_execution_start',{tool_call:{name:'read',arguments:{path:'README.md'}}},'r')).toEqual({turn_id:'r',type:'tool_call',title:'read',detail:'{"path":"README.md"}'});
 expect(tauStatus('tau.agent.tool_execution_update',{message:'Reading…'},'r').detail).toBe('Reading…');
 expect(tauStatus('tau.agent.error',{message:'Failure'},'r').title).toBe('Failure');
 expect(tauStatus('tau.agent.message_delta',{delta:'text'},'r')).toBe(null);
});
