import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';
import path from 'node:path';

test('background same-revision plan refresh preserves local draft',async({page})=>{
 // Execute the actual pure adapter function with controlled state, avoiding
 // nondeterministic SSE timing while retaining the production implementation.
 const source=await readFile(path.resolve(import.meta.dirname,'../../../src/tau_web/static/app.js'),'utf8');
 const start=source.indexOf('function applyPlanResponse('),end=source.indexOf('\nasync function loadPlan',start);
 expect(start).toBeGreaterThan(0);expect(end).toBeGreaterThan(start);
 const result=await page.evaluate(fn=>{
  const state={plan:{session_id:'review',revision:1,markdown:'saved'},planDraft:'unsaved',planDirty:true,planConflict:null};
  const apply=new Function('state','renderPlan',`${fn}; return applyPlanResponse;`)(state,()=>{});
  apply({session_id:'review',revision:1,markdown:'saved'},{sessionId:'review'});
  const same={...state};
  apply({session_id:'review',revision:2,markdown:'remote'},{sessionId:'review'});
  const conflict={...state};
  apply({session_id:'review',revision:2,markdown:'remote'},{sessionId:'review',force:true});
  return {same,conflict,reloaded:state};
 },source.slice(start,end));
 expect(result.same.planDraft).toBe('unsaved');expect(result.same.planDirty).toBe(true);expect(result.same.planConflict).toBeNull();
 expect(result.conflict.planDraft).toBe('unsaved');expect(result.conflict.planConflict.revision).toBe(2);
 expect(result.reloaded.planDraft).toBe('remote');expect(result.reloaded.planDirty).toBe(false);
});
