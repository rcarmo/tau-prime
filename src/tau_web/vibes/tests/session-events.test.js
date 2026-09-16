import {test,expect} from 'bun:test';
import {eventMatchesSession} from '../static/js/components/session-events.js';

test('session-scoped turn events reject stale owners',()=>{
 expect(eventMatchesSession('agent_status',{session_id:'one'},'one')).toBe(true);
 expect(eventMatchesSession('agent_status',{session_id:'old'},'one')).toBe(false);
 expect(eventMatchesSession('agent_status',{data:{session_id:'one'}},'one')).toBe(true);
 expect(eventMatchesSession('sessions_changed',{session_id:'old'},'one')).toBe(true);
});
