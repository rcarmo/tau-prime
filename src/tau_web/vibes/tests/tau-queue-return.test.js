import {test,expect} from 'bun:test';
import {returnQueuedText} from '../static/js/tau-queue-return.js';
test('queue return preserves text before removal and retains recovery after failure',async()=>{
 const calls=[];
 const result=await returnQueuedText({text:'draft',preserve:async text=>calls.push(text),remove:async()=>{calls.push('remove');return false;}});
 expect(calls).toEqual(['draft','remove']);expect(result).toEqual({removed:false,preserved:true});
});
test('storage failure never removes queued input',async()=>{
 let removed=false;
 await expect(returnQueuedText({text:'draft',preserve:async()=>{throw new Error('quota');},remove:async()=>{removed=true;return true;}})).rejects.toThrow('quota');
 expect(removed).toBe(false);
});
test('recovery copy preserves full text and is isolated by session and queue',async()=>{
 const {preserveQueuedRecovery}=await import('../static/js/tau-queue-return.js');
 const data=new Map();const storage={setItem:(k,v)=>data.set(k,v),getItem:k=>data.get(k)};
 const text='x'.repeat(100001);
 const first=preserveQueuedRecovery(storage,{sessionId:'a',queueId:'q',text});
 const second=preserveQueuedRecovery(storage,{sessionId:'b',queueId:'q',text:'other'});
 expect(first).not.toBe(second);expect(JSON.parse(data.get(first)).text).toBe(text);
 expect(()=>preserveQueuedRecovery({setItem(){},getItem(){return null;}},{sessionId:'a',queueId:'q',text})).toThrow('verify');
});
test('recovery appends to latest draft and retains reference metadata',async()=>{
 const {preserveQueuedRecovery,recoverQueuedDraft}=await import('../static/js/tau-queue-return.js');
 const data=new Map();const storage={setItem:(k,v)=>data.set(k,v),getItem:k=>data.get(k),removeItem:k=>data.delete(k)};
 const key=preserveQueuedRecovery(storage,{sessionId:'a',queueId:'q',text:'queued'});
 storage.setItem('vibes_compose_draft:a',JSON.stringify({text:'new edit',fileRefs:['README.md']}));
 expect(recoverQueuedDraft(storage,key,'a')).toBe('new edit\n\nqueued');
 expect(JSON.parse(data.get('vibes_compose_draft:a')).fileRefs).toEqual(['README.md']);
 expect(data.has(key)).toBe(false);
});
test('oversize recovery stays recoverable and never truncates draft',async()=>{
 const {preserveQueuedRecovery,recoverQueuedDraft}=await import('../static/js/tau-queue-return.js');
 const data=new Map();const storage={setItem:(k,v)=>data.set(k,v),getItem:k=>data.get(k),removeItem:k=>data.delete(k)};
 const key=preserveQueuedRecovery(storage,{sessionId:'a',queueId:'q',text:'x'.repeat(100001)});
 expect(()=>recoverQueuedDraft(storage,key,'a')).toThrow('limit');expect(data.has(key)).toBe(true);
 expect(()=>recoverQueuedDraft(storage,key,'b')).toThrow('Invalid queue recovery');
});
test('retry after recovery cleanup failure does not duplicate text',async()=>{
 const {preserveQueuedRecovery,recoverQueuedDraft}=await import('../static/js/tau-queue-return.js');
 const data=new Map();let fail=true;
 const storage={setItem:(k,v)=>data.set(k,v),getItem:k=>data.get(k),removeItem:k=>{if(fail)throw new Error('cleanup');data.delete(k);}};
 const key=preserveQueuedRecovery(storage,{sessionId:'a',queueId:'q',text:'queued'});
 expect(()=>recoverQueuedDraft(storage,key,'a')).toThrow('cleanup');
 expect(JSON.parse(data.get('vibes_compose_draft:a')).text).toBe('queued');
 fail=false;expect(recoverQueuedDraft(storage,key,'a')).toBe('queued');expect(data.has(key)).toBe(false);
});
