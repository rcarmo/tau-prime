import {test,expect} from 'bun:test';
import {activateTauExtensions} from '../static/js/tau-extensions.js';
test('extension activation discovers modules and validates submit/navigation',async()=>{
 let adapters;const calls=[];
 const result=await activateTauExtensions({getSessionId:()=> 'one',navigate:async()=>{},getToken:()=> 'fixture',sdk:{configure:a=>adapters=a,loadAll:async modules=>({modules})},fetchImpl:async(path,options)=>{calls.push({path,...options});return Response.json(path.endsWith('frontend-modules')?{modules:[]}:path.includes('/sessions?')?{sessions:[{session_id:'one'}]}:{run_id:'run'});}});
 expect(result.modules).toEqual([]);await adapters.submit({text:'hello'});expect(calls.at(-1).path).toBe('/api/sessions/one/runs');
 expect(()=>adapters.submit({text:'hello',mode:'invalid'})).toThrow('delivery');
 await expect(adapters.navigate('missing')).rejects.toThrow('Unknown');
});
