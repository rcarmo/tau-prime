import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {readFileSync} from 'node:fs';
import {extname,join,normalize} from 'node:path';
import {chromium,webkit} from 'playwright';

const root=new URL('../static/',import.meta.url).pathname;
const types={'.html':'text/html','.js':'text/javascript'};
const server=createServer((req,res)=>{
 if(req.url==='/'){res.writeHead(200,{'content-type':'text/html'});res.end(`<!doctype html><body><div id="app"></div><script type="module">
 import {html,render} from '/js/vendor/preact-htm.js';
 import {TauReadAloud} from '/js/components/tau-read-aloud.js';
 render(html\`<div id="first"><\${TauReadAloud} text="First post" /></div><div id="second"><\${TauReadAloud} text="Second post" /></div>\`,document.querySelector('#app'));
 </script>`);return;}
 const path=normalize(join(root,decodeURIComponent(req.url)));if(!path.startsWith(root)){res.writeHead(403);res.end();return;}
 let content;try{content=readFileSync(path);}catch{res.writeHead(404);res.end();return;}
 res.writeHead(200,{'content-type':types[extname(path)]||'application/octet-stream'});res.end(content);
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
try{
 for(const [name,engine] of [['chromium',chromium],['webkit',webkit]]){
  const browser=await engine.launch({headless:false});
  try{
   const page=await browser.newPage();
   await page.addInitScript(()=>{
    window.calls=[];window.utterances=[];
    Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{speak:u=>{window.utterances.push(u);window.calls.push(['speak',u.text]);},cancel:()=>window.calls.push(['cancel'])}});
    window.SpeechSynthesisUtterance=class{constructor(text){this.text=text;}};
   });
   await page.goto(`http://127.0.0.1:${server.address().port}/`);
   const first=page.locator('#first'),second=page.locator('#second');
   await first.getByRole('button',{name:'Read aloud'}).click();
   await second.getByRole('button',{name:'Read aloud'}).click();
   await assert.doesNotReject(()=>first.getByRole('button',{name:'Read aloud'}).waitFor());
   await page.evaluate(()=>window.utterances[0].onend());
   await assert.doesNotReject(()=>second.getByRole('button',{name:'Stop reading aloud'}).waitFor());
   await second.getByRole('button',{name:'Stop reading aloud'}).click();
   assert.deepEqual(await page.evaluate(()=>window.calls),[['speak','First post'],['cancel'],['speak','Second post'],['cancel']]);
   console.log(`${name}: speech ownership transfer passed`);
  }finally{await browser.close();}
 }
}finally{server.close();}
