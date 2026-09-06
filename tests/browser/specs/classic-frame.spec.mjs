import {test,expect} from '@playwright/test';
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
const frontend=path.resolve(import.meta.dirname,'../../../src/tau_web/frontend');
const require=createRequire(path.join(frontend,'package.json'));
const {build}=require('esbuild');
const css=await readFile(path.resolve(frontend,'../static/piclaw-classic.css'),'utf8');
const bundle=await build({stdin:{contents:`import {h,render} from 'preact';import {ClassicChatFrame} from './src/components/ClassicChatFrame.tsx';render(h(ClassicChatFrame,{workspaceOpen:false},h('div',{class:'timeline reverse'},'Review message'),h('div',{class:'compose-box'},h('textarea',{'aria-label':'Message'}))),document.getElementById('app'));`,resolveDir:frontend,loader:'tsx'},bundle:true,write:false,format:'iife',jsx:'automatic',jsxImportSource:'preact',nodePaths:[path.join(frontend,'node_modules')]});
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
});
