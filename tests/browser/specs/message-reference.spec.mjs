import { expect, test } from '@playwright/test';
import { createRequire } from 'node:module';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
const frontend = path.resolve(import.meta.dirname, '../../../src/tau_web/frontend');
const require = createRequire(path.join(frontend, 'package.json'));
const { build } = require('esbuild');
const reference = process.env.PICLAW_VISUAL_SOURCE || '/opt/piclaw/releases/piclaw-2.15.3-linux-x64-baseline/app/runtime/web/static/visual/frontend/src';

test('capture genuine Piclaw populated user-message reference', async ({ page }, info) => {
  const result = await build({
    stdin: { contents: `import {render} from 'preact';
      import {MessageItem} from ${JSON.stringify(path.join(reference, 'components/message-list/MessageItem.tsx'))};
      import {userAvatarUrl} from ${JSON.stringify(path.join(reference, 'api/identity.ts'))};
      userAvatarUrl.value = null; // Shared no-uploaded-avatar state.
      import {MessageItem as TauMessage} from ${JSON.stringify(path.join(frontend, 'src/components/Timeline.tsx'))};
      window.renderTau = () => render(<div className="message-list"><TauMessage item={{id:'1',role:'user',content:'Please inspect the workspace.\\n\\nKeep the existing API behavior.',meta:'1m ago'}} resultByCall={new Map()} /></div>,document.getElementById('app'));
      render(<div className="message-list"><MessageItem interaction={{id:1,type:'user',content:'Please inspect the workspace.\\n\\nKeep the existing API behavior.',created_at:'2026-09-01T12:00:00Z'}} isCollapsed={false} onToggleCollapse={()=>{}} onDelete={()=>{}} /></div>,document.getElementById('app'));`, loader:'tsx', resolveDir:frontend },
    alias: { 'preact': path.join(frontend, 'node_modules/preact') },
    bundle:true, write:false, format:'iife', jsx:'automatic', jsxImportSource:'preact',
    nodePaths:[path.join(frontend,'node_modules'), path.resolve(import.meta.dirname,'../node_modules')],
    // Release omits this non-rendering helper; fixture never changes identity/title.
    plugins:[{name:'fixture-title',setup(build){
      build.onResolve({filter:/src\/ui\/browser-title$/},()=>({path:'title',namespace:'fixture'}));
      build.onLoad({filter:/.*/,namespace:'fixture'},()=>({contents:'export const formatSessionBrowserTitle = name => name;',loader:'js'}));
    }}],
  });
  page.on('pageerror', error => console.error('Reference render:', error.message));
  await page.route('http://reference.test/**', async route => {
    const url = new URL(route.request().url());
    if (url.pathname === '/') return route.fulfill({ contentType:'text/html', body:'<meta name="viewport" content="width=device-width, initial-scale=1"><div id="app"></div>' });
    return route.fulfill({status:404,body:''});
  });
  await page.goto('http://reference.test/');
  await page.clock.install({ time:new Date('2026-09-01T12:01:00Z') });
  await page.setContent('<meta name="viewport" content="width=device-width, initial-scale=1"><div id="app"></div>');
  expect(await page.evaluate(() => document.documentElement.clientWidth)).toBe(page.viewportSize().width);
  await page.addStyleTag({content:await readFile(path.join(frontend,'../static/piclaw-reference.css'),'utf8')});
  await page.addScriptTag({content:result.outputFiles[0].text});
  await expect(page.locator('.message-list__content')).toContainText('Please inspect');
  await mkdir('/workspace/tmp/tau-message-reference',{recursive:true});
  const measure = () => page.locator('.message-list__item, .message-list__content').evaluateAll(elements => elements.map(el => {
    const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return { className: el.className, width:r.width, height:r.height, text:el.textContent, whiteSpace:s.whiteSpace, html:el.innerHTML };
  }));
  const upstream = await measure();
  await page.screenshot({path:`/workspace/tmp/tau-message-reference/${info.project.name}.png`});
  await page.evaluate(() => window.renderTau());
  await expect(page.locator('.message-list__content')).toContainText('Please inspect');
  await page.screenshot({path:`/workspace/tmp/tau-message-reference/${info.project.name}-tau.png`});
  const tau = await measure();
  expect(tau.map(({width,height,whiteSpace}) => ({width,height,whiteSpace}))).toEqual(upstream.map(({width,height,whiteSpace}) => ({width,height,whiteSpace})));
  await writeFile(`/workspace/tmp/tau-message-reference/${info.project.name}-comparison.json`, JSON.stringify({upstream,tau:await measure()},null,2));
});
