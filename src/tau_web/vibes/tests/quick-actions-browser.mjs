import {chromium,webkit} from 'playwright';
import {spawn} from 'node:child_process';
import assert from 'node:assert/strict';
const server=spawn('bun',['dev-server.js'],{env:{...process.env,TAU_VIBES_PORT:'8895'},stdio:'ignore'});
try {
 for(let i=0;i<50;i++){try{if((await fetch('http://127.0.0.1:8895')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
 for(const engine of [chromium,webkit]){
  const browser=await engine.launch({headless:!process.env.TAU_SMOKE_HEADED});
  try {
   const page=await browser.newPage();
   await page.route('**/quick-actions-test',route=>route.fulfill({contentType:'text/html',body:`<!doctype html><main class="container"><div class="timeline" tabindex="0">Timeline</div><textarea class="compose-box">draft</textarea><input><select><option>x</option></select><button>button</button><a href="#">link</a><div contenteditable="true">editable</div><div role="textbox">textbox</div><div class="workspace-sidebar">workspace</div><dialog>dialog</dialog><div role="listbox">listbox</div><div class="open-popup">popup</div><div id="mount"></div></main><script type="module">
import {html,render} from '/static/js/vendor/preact-htm.js';import {QuickActions} from '/static/js/components/quick-actions.js';
window.calls=[];window.prefill='';window.mount=()=>render(html\`<\${QuickActions} sessions=\${[{id:'alpha',name:'Alpha'}]} sessionId="alpha" workspace=\${[{id:'workspace',title:'Workspace action',run:()=>calls.push('workspace')}]} onSwitchSession=\${id=>calls.push(id)} onPrefill=\${text=>{window.prefill=text;document.querySelector('textarea').value=text+' ';}} loadCommands=\${async()=>({commands:[{name:'/skill:demo',description:'Demo skill'},{name:'/model',description:'Model'}]})}/>\`,document.getElementById('mount'));window.mount();</script>`}));
   await page.goto('http://127.0.0.1:8895/quick-actions-test');
   const timeline=page.locator('.timeline');await timeline.focus();await page.keyboard.type('a');
   const dialog=page.getByRole('dialog',{name:'Quick actions'});await dialog.waitFor();
   const input=page.getByRole('combobox',{name:'Search quick actions'});assert.equal(await input.inputValue(),'a');assert.equal(await input.evaluate(el=>el===document.activeElement),true);
   await input.fill('');for(const section of ['Agents','Workspace','Slash commands'])await page.locator('.timeline-quick-actions-section',{hasText:section}).waitFor();
   assert.equal(await page.getByText('Skills',{exact:true}).count(),0);
   await input.fill('skill:demo');const skill=page.getByRole('option',{name:/\/skill:demo/});await skill.waitFor();await skill.click();
   assert.equal(await page.evaluate(()=>window.prefill),'/skill:demo');assert.equal(await page.locator('textarea').inputValue(),'/skill:demo ');assert.deepEqual(await page.evaluate(()=>window.calls),[]);await dialog.waitFor({state:'hidden'});
   assert.equal(await page.locator('textarea').evaluate(el=>el.selectionStart),'/skill:demo '.length);
   await timeline.focus();await page.keyboard.type('z');await dialog.waitFor();await page.keyboard.press('Escape');await dialog.waitFor({state:'hidden'});assert.equal(await input.count(),0);assert.deepEqual(await page.evaluate(()=>window.calls),[]);
   for(const selector of ['textarea','input','select','button','a','[contenteditable]','[role="textbox"]','.workspace-sidebar','dialog','[role="listbox"]']){const target=page.locator(selector).first();await target.evaluate(el=>el.dispatchEvent(new KeyboardEvent('keydown',{key:'q',bubbles:true})));assert.equal(await dialog.count(),0,selector);}
   await timeline.focus();await page.keyboard.type('w');await dialog.waitFor();await input.fill('');const options=page.getByRole('option');const count=await options.count();assert.ok(count>2);await page.waitForFunction(()=>document.querySelector('.timeline-quick-actions-item[aria-selected="true"]'));await page.waitForTimeout(300);await input.press('ArrowUp');await page.waitForTimeout(300);await page.locator('.timeline-quick-actions-item[aria-selected="true"]').click();await dialog.waitFor({state:'hidden'});assert.equal(await dialog.count(),0);
   console.log(`${engine.name()}: Quick Actions typeahead, exclusions, skills, wrap, execute and dismissal passed`);
  } finally {await browser.close();}
 }
} finally {server.kill();}
