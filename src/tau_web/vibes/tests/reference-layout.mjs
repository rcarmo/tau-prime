import {createServer} from 'node:http';
import {createHash} from 'node:crypto';
import {readFile,mkdir} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
import {chromium,webkit,expect} from '@playwright/test';
const engine=process.env.TAU_REFERENCE_ENGINE||'chromium';
const size=process.env.TAU_REFERENCE_SIZE||'desktop';
const theme=process.env.TAU_REFERENCE_THEME||'light';
const viewport={phone:{width:390,height:844},tablet:{width:820,height:1180},desktop:{width:1440,height:900}}[size];
const reference=process.env.TAU_REFERENCE_STATIC||'/workspace/tmp/vibes-reference/source/src/vibes/static';
const pinned=JSON.parse(await readFile(new URL('./reference-hashes.json',import.meta.url),'utf8'));
for(const [file,hash] of Object.entries(pinned.files))expect(createHash('sha256').update(await readFile(resolve(reference,file))).digest('hex'),`Pinned reference ${file}`).toBe(hash);
const current=resolve('static');
const out=`/workspace/tmp/vibes-reference/comparison/${engine}-${size}-${theme}`;await mkdir(out,{recursive:true});
const server=createServer(async(req,res)=>{
 const u=new URL(req.url,'http://localhost'),ref=u.pathname.startsWith('/reference/');
 const path=u.pathname.replace(/^\/(reference|current)/,'');
 try{const data=await readFile(resolve(ref?reference:current,path==='/'?'index.html':path.replace(/^\/static\//,'')));res.writeHead(200,{'Content-Type':extname(path)==='.js'?'text/javascript':extname(path)==='.css'?'text/css':'text/html'});res.end(data);}catch{res.writeHead(404);res.end();}
});await new Promise(r=>server.listen(8896,'127.0.0.1',r));
const browser=await (engine==='webkit'?webkit:chromium).launch();
const measurements={};
try{
 for(const [name,root] of [['reference',reference],['current',current]]){
 const page=await browser.newPage({viewport,colorScheme:theme});
 await page.route('**/*',async route=>{
  const u=new URL(route.request().url());
  if(u.pathname==='/'||u.pathname.startsWith('/static/')){
   let path=u.pathname==='/'?'index.html':u.pathname.slice(8);
   let file=resolve(root,path);
   if(name==='current'&&['extension-ui.js','frontend-sdk.js','widget-bridge.js'].includes(path))file=resolve('../static',path);
   try{const body=await readFile(file);return route.fulfill({body,contentType:path.endsWith('.js')?'text/javascript':path.endsWith('.css')?'text/css':path.endsWith('.html')?'text/html':'application/octet-stream'});}catch{return route.fulfill({status:404,body:''});}
  }
  if(u.pathname.includes('events'))return route.fulfill({contentType:'text/event-stream',body:': fixture\n\n'});
  const session={id:'reference-session',name:'Reference session',session_id:'reference-session',title:'Reference session',provider_name:'test',model:'fixture',updated_at:'r1'};
  let data={};
  if(u.pathname.endsWith('/sessions'))data={sessions:[session]};
  else if(u.pathname==='/api/sessions/reference-session')data=session;
  else if(u.pathname.includes('timeline'))data=name==='current'?{timeline:[]}:{posts:[],has_more:false};
  else if(u.pathname.includes('agents'))data={agents:[]};
  else if(u.pathname.endsWith('/runs'))data={runs:[]};
  else if(u.pathname.includes('queue'))data={items:[]};
  else if(u.pathname.includes('approvals'))data={approvals:[]};
  else if(u.pathname.includes('models'))data={models:[]};
  else if(u.pathname.includes('modules'))data={modules:[]};
  else if(u.pathname.includes('files')||u.pathname.includes('tree'))data={entries:[],files:[]};
  return route.fulfill({contentType:'application/json',body:JSON.stringify(data)});
 });
 await page.goto('http://127.0.0.1:8896/?session=reference-session');
 await expect(page.locator('.compose-box textarea')).toBeVisible();await page.waitForTimeout(1500);
 const geometry=await page.evaluate(()=>Object.fromEntries(['.app-shell','.container','.timeline','.compose-box','.compose-box textarea','.workspace-toggle-tab'].map(s=>{const e=document.querySelector(s),r=e?.getBoundingClientRect();return [s,r?{x:r.x,y:r.y,width:r.width,height:r.height}:null];})));
 measurements[name]=geometry;
 console.log(name,JSON.stringify(geometry));
 await expect(page.locator('.timeline')).toContainText('No messages yet. Start a conversation!');
 await expect(page.locator('.app-shell > .container > details')).toHaveCount(0);
 await page.screenshot({path:`${out}/${name}.png`});await page.close();
 }
 for(const selector of ['.app-shell','.container','.timeline','.compose-box','.compose-box textarea','.workspace-toggle-tab']){
  expect(measurements.current[selector],`${selector} must match pinned reference geometry`).toEqual(measurements.reference[selector]);
 }
 console.log(`PASS exact reference geometry: ${engine}/${size}/${theme}`);
}finally{await browser.close();await new Promise(r=>server.close(r));}
