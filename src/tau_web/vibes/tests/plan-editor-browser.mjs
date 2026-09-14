import {chromium,webkit} from 'playwright';
import {spawn} from 'node:child_process';
import assert from 'node:assert/strict';
const server=spawn('bun',['dev-server.js'],{env:{...process.env,TAU_VIBES_PORT:'8894'},stdio:'ignore'});
try {
 for(let i=0;i<50;i++){try{if((await fetch('http://127.0.0.1:8894')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
 for(const engine of [chromium,webkit]){
  const browser=await engine.launch({headless:true});
  try{
   const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.route('**/editor-test',route=>route.fulfill({contentType:'text/html',body:`<html data-theme="dark"><link rel="stylesheet" href="/static/css/plan-sidebar.css"><body><main id="test"></main><script type="module">
import {html,render} from '/static/js/vendor/preact-htm.js';
import {TauPlanEditor} from '/static/js/components/tau-plan-editor.js';
window.mount=(key,value,disabled=false)=>render(html\`<\${TauPlanEditor} key=\${key} value=\${value} disabled=\${disabled} onChange=\${text=>window.changed=text}/>\`,document.getElementById('test'));
window.mount('a','- [x] done\\n- [-] active\\n- [ ] pending');
</script></body></html>`}));
   await page.goto('http://127.0.0.1:8894/editor-test');
   await page.locator('.plan-sidebar-cm-line-current').waitFor();
   assert.equal(await page.locator('.plan-sidebar-cm-checkbox-completed').count(),1);
   assert.equal(await page.locator('.plan-sidebar-cm-text-completed').evaluate(el=>getComputedStyle(el).textDecorationLine),'line-through');
   assert.equal(await page.locator('.plan-sidebar-cm-text-current').evaluate(el=>getComputedStyle(el).fontWeight),'650');
   assert.equal(await page.locator('.plan-sidebar-cm-line-current').evaluate(el=>getComputedStyle(el).borderLeftWidth),'3px');
   assert.equal(await page.locator('.plan-sidebar-cm-checkbox-completed').evaluate(el=>getComputedStyle(el).display),'inline-block');
   assert.equal(await page.locator('.cm-content').evaluate(el=>el===document.activeElement),true);
   const darkClasses=await page.locator('.cm-editor').getAttribute('class');
   await page.emulateMedia({colorScheme:'light'});
   await page.evaluate(()=>document.documentElement.removeAttribute('data-theme'));
   await page.waitForFunction(before=>document.querySelector('.cm-editor')?.className!==before,darkClasses);
   const lightClasses=await page.locator('.cm-editor').getAttribute('class');
   await page.emulateMedia({colorScheme:'dark'});
   await page.waitForFunction(before=>document.querySelector('.cm-editor')?.className!==before,lightClasses);
   assert.equal(await page.locator('.cm-editor').getAttribute('class'),darkClasses);
   await page.evaluate(()=>document.documentElement.dataset.theme='light');
   await page.waitForFunction(expected=>document.querySelector('.cm-editor')?.className===expected,lightClasses);
   await page.evaluate(()=>window.mount('b','- [ ] other session'));
   await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent==='- [ ] other session');
   await page.locator('.cm-content').click();await page.keyboard.press('End');await page.keyboard.type(' edited');
   await page.waitForFunction(()=>window.changed==='- [ ] other session edited');
   await page.evaluate(()=>window.mount('b','- [x] remotely saved',true));
   await page.waitForFunction(()=>document.querySelector('.cm-content')?.textContent==='- [x] remotely saved');
   await page.keyboard.type(' forbidden');
   assert.equal(await page.locator('.cm-content').textContent(),'- [x] remotely saved');
   assert.deepEqual(errors,[]);console.log(`${engine.name()}: editor decoration, session switch, editing and read-only passed`);
  }finally{await browser.close();}
 }
}finally{server.kill();}
