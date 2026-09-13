import {spawnSync} from 'node:child_process';
// Sequential fresh servers avoid accidental cross-case state/server reuse.
for(const engine of ['chromium','webkit'])for(const size of ['phone','tablet','desktop'])for(const theme of ['light','dark']){
 const result=spawnSync(process.execPath,['tests/browser-smoke.mjs'],{cwd:new URL('..',import.meta.url),env:{...process.env,TAU_SMOKE_ENGINE:engine,TAU_SMOKE_SIZE:size,TAU_SMOKE_THEME:theme},encoding:'utf8',timeout:90000});
 console.log(`${engine}/${size}/${theme}: ${result.status===0?'PASS':'FAIL'}`);
 if(result.status!==0){console.error(result.stdout,result.stderr,result.error||'');process.exit(1);}
}
console.log('12 browser/theme/viewport workflow cases passed');
