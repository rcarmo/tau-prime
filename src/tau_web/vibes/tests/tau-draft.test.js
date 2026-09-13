import {test,expect} from 'bun:test';
import {reduceTauDraft} from '../static/js/tau-draft.js';
test('draft rejects other sessions/runs and snapshot clears stale text',()=>{
 const state={runId:'run',text:'current'};
 const frame=(session,run)=>({event:'tau.agent.message_delta',data:{session_id:session,run_id:run,payload:{delta:' next'}}});
 expect(reduceTauDraft(state,frame('other','run'),'one')).toBe(state);
 expect(reduceTauDraft(state,frame('one','other'),'one')).toBe(state);
 expect(reduceTauDraft(state,frame('one','run'),'one').text).toBe('current next');
 expect(reduceTauDraft(state,{event:'tau.snapshot'},'one')).toEqual({runId:null,text:''});
});
