import {test,expect} from 'bun:test';
import {resolveMessageReferences} from '../static/js/tau-message-references.js';
test('references resolve exact session message text and deduplicate IDs',async()=>{
 const calls=[];
 const text=await resolveMessageReferences('one',[3,'3'],async(...args)=>{calls.push(args);return {posts:[{id:3,data:{session_id:'one',type:'agent_response',content:'Answer café 日本語'}}]};});
 expect(calls).toEqual([['one',1,4]]);
 expect(JSON.parse(text.split('\n')[1]).text).toBe('Answer café 日本語');
 expect(text).not.toContain('Messages:\n- 3');
});
test('missing and cross-session references fail closed',async()=>{
 await expect(resolveMessageReferences('one',[3],async()=>({posts:[]}))).rejects.toThrow('unavailable');
 await expect(resolveMessageReferences('one',[3],async()=>({posts:[{id:3,data:{session_id:'other',content:'private'}}]}))).rejects.toThrow('unavailable');
});
test('oversized reference content is not silently truncated',async()=>{
 await expect(resolveMessageReferences('one',[3],async()=>({posts:[{id:3,data:{session_id:'one',content:'x'.repeat(32769)}}]}))).rejects.toThrow('32 KiB');
});
