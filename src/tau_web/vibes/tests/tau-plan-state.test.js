import {test,expect} from 'bun:test';
import {createPlanState,planProgress} from '../static/js/tau-plan-state.js';
test('progress matches unordered and numbered checklist states',()=>{
 expect(planProgress('- [x] done\n1. [-] active\n* [ ] todo\ntext')).toEqual({total:3,done:1,percent:33});
});
test('late load does not overwrite edits or another session',async()=>{
 let resolve;const state=createPlanState({read:()=>new Promise(r=>resolve=r),write:async()=>{}});
 const loading=state.load('a');state.edit('a','draft');state.edit('b','other');resolve({markdown:'remote',revision:1});
 expect(await loading).toBe(false);expect(state.get('a').text).toBe('draft');expect(state.get('b').text).toBe('other');
});
test('save is revision safe and retains edits made during request',async()=>{
 let resolve;const calls=[];const state=createPlanState({read:async()=>({markdown:'old',revision:3}),write:(...args)=>{calls.push(args);return new Promise(r=>resolve=r);}});
 await state.load('a');state.edit('a','submitted');const saving=state.save('a');state.edit('a','newer');resolve({markdown:'submitted',revision:4});
 expect(await saving).toBe(false);expect(calls).toEqual([['a','submitted',3]]);expect(state.get('a').text).toBe('newer');expect(state.get('a').base).toBe('submitted');
});
test('conflict retains draft and revision without retry',async()=>{
 let calls=0;const state=createPlanState({read:async()=>({markdown:'old',revision:1}),write:async()=>{calls++;throw Object.assign(new Error('conflict'),{status:409});}});
 await state.load('a');state.edit('a','draft');expect(await state.save('a')).toBe(false);
 expect(state.get('a').text).toBe('draft');expect(state.get('a').revision).toBe(1);expect(calls).toBe(1);
});
