import {test,expect} from '@playwright/test';
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
const frontend=path.resolve(import.meta.dirname,'../../../src/tau_web/frontend');
const require=createRequire(path.join(frontend,'package.json'));
const {build}=require('esbuild');
const css=await readFile(path.resolve(frontend,'../static/piclaw-classic.css'),'utf8');
const bundle=await build({stdin:{contents:`import {h,render} from 'preact';import {ClassicChatFrame} from './src/components/ClassicChatFrame.tsx';import {ClassicComposerSurface} from './src/components/ClassicComposerSurface.tsx';import {ClassicPost} from './src/components/ClassicPost.tsx';import {Timeline} from './src/components/Timeline.tsx';window.mountClassicTimeline=()=>{render(h(ClassicChatFrame,null,h(Timeline,{classic:true})),document.getElementById('app'));};render(h(ClassicChatFrame,{workspaceOpen:false},h('div',{class:'timeline reverse'},h('div',{class:'timeline-content'},h(ClassicPost,{id:'user',agent:false,author:'You',time:'2m',avatar:'Y'},'Review the workspace.'),h(ClassicPost,{id:'agent',agent:true,author:'Tau',time:'1m',avatar:'τ',actions:h('button',{class:'post-action-btn',type:'button','aria-label':'Copy'},'Copy')},h('p',null,'The API is unchanged.')))),h(ClassicComposerSurface,{session:h('button',{class:'compose-session-switcher-pill',type:'button'},'Sessions'),input:h('textarea',{'aria-label':'Message',rows:1,style:{height:'50px'}}),metadata:h('button',{class:'compose-model-hint compose-model-hint-btn',type:'button'},'test/review-model'),actions:h('button',{class:'send-btn',type:'button'},'Send')})),document.getElementById('app'));`,resolveDir:frontend,loader:'tsx'},bundle:true,write:false,format:'iife',jsx:'automatic',jsxImportSource:'preact',nodePaths:[path.join(frontend,'node_modules')]});
for(const theme of ['light','dark']) test(`classic ${theme} frame uses centered column without visual shell`,async({page})=>{
 await page.route('**/classic-frame-fixture',route=>route.fulfill({contentType:'text/html',body:`<html data-theme="${theme}"><head><meta name="viewport" content="width=device-width, initial-scale=1"></head><body><div id="app"></div></body></html>`}));
 await page.goto('/classic-frame-fixture');
 await page.addStyleTag({content:css});await page.addScriptTag({content:bundle.outputFiles[0].text});
 await expect(page.locator('.app-shell.workspace-collapsed')).toBeVisible();
 await expect(page.locator('.activity-bar,.tab-bar,.app-layout__status-bar')).toHaveCount(0);
 const box=await page.locator('.container').boundingBox();const viewport=page.viewportSize();
 expect(box.width).toBeLessThanOrEqual(viewport.width);
 expect(Math.abs(box.x-(viewport.width-box.width)/2)).toBeLessThanOrEqual(1);
 // WebKit fractional CSS-pixel rounding can differ by 1/64 px.
 expect(Math.abs(box.height-viewport.height)).toBeLessThanOrEqual(0.02);
 await expect(page.locator('.workspace-sidebar')).toHaveAttribute('inert','');
 await expect(page.getByRole('textbox',{name:'Message'})).toBeVisible();
 await expect(page.locator('.compose-top-session-row')).toContainText('Sessions');
 await expect(page.locator('.compose-footer')).toContainText('test/review-model');
 const input=await page.getByRole('textbox',{name:'Message'}).boundingBox();
 const footer=await page.locator('.compose-footer').boundingBox();
 expect(footer.y).toBeGreaterThanOrEqual(input.y+input.height-0.02);
 await expect(page.locator('.compose-box select')).toHaveCount(0);
 const user=await page.locator('#user').boundingBox();
 const agent=await page.locator('#agent').boundingBox();
 expect(user.y+user.height).toBeLessThanOrEqual(agent.y+0.02);
 expect(agent.y+agent.height).toBeLessThanOrEqual((await page.locator('.compose-box').boundingBox()).y+0.02);
 await expect(page.locator('#agent .post-author')).toHaveText('Tau');
 await expect(page.locator('#agent .post-actions button')).toHaveAccessibleName('Copy');
});

test('classic timeline consumes Tau events and preserves collapse focus',async({page})=>{
 await page.route('**/classic-timeline-fixture',r=>r.fulfill({contentType:'text/html',body:'<meta name="viewport" content="width=device-width, initial-scale=1"><div id="app"></div>'}));
 await page.goto('/classic-timeline-fixture');await page.addStyleTag({content:css});await page.addScriptTag({content:bundle.outputFiles[0].text});
 await page.evaluate(()=>window.mountClassicTimeline());
 await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tau:timeline-render',{detail:{selected:true,items:[{id:'one',role:'user',content:'User text',meta:'2m'},{id:'two',role:'assistant',content:'**Agent text**',meta:'1m'}]}})));
 await expect(page.locator('.post')).toHaveCount(2);
 await expect(page.locator('#post-two strong')).toHaveText('Agent text');
 const collapse=page.locator('#post-two').getByRole('button',{name:'Collapse message'});
 await collapse.focus();await page.keyboard.press('Enter');
 const expand=page.locator('#post-two').getByRole('button',{name:'Expand message'});
 await expect(expand).toBeFocused();await expect(expand).toHaveAttribute('aria-expanded','false');
 await expand.click();await expect(page.locator('#post-two strong')).toHaveText('Agent text');
});
