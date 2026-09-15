import {spawnSync} from 'node:child_process';
// Each journey owns fresh backend/proxy processes and a temporary database.
if(!process.env.TAU_BROWSER_BIN)throw new Error('Set TAU_BROWSER_BIN to the installed wheel executable');
for(const engine of ['chromium','webkit'])for(const size of ['phone','tablet','desktop'])for(const theme of ['light','dark']){
 const result=spawnSync(process.execPath,['tests/live-backend.mjs'],{cwd:new URL('..',import.meta.url),env:{...process.env,TAU_VIBES_PROXY_ALL:'1',TAU_LIVE_AUTH:'1',TAU_LIVE_LOGIN_UI:'1',TAU_LIVE_AXE:'1',TAU_LIVE_ENGINE:engine,TAU_LIVE_SIZE:size,TAU_LIVE_THEME:theme},encoding:'utf8',timeout:90000});
 console.log(`${engine}/${size}/${theme}: ${result.status===0?'PASS':'FAIL'}`);
 if(result.status!==0){console.error(result.stdout,result.stderr,result.error||'');process.exit(1);}
}
console.log('12 installed-wheel authenticated workflow/accessibility cases passed');
