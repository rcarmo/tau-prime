import { expect, test } from '@playwright/test';
import { createRequire } from 'node:module';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
const frontend = path.resolve(import.meta.dirname, '../../../src/tau_web/frontend');
const require = createRequire(path.join(frontend, 'package.json'));
const { build } = require('esbuild');
const reference = process.env.PICLAW_VISUAL_SOURCE || '/opt/piclaw/releases/piclaw-2.15.3-linux-x64-baseline/app/runtime/web/static/visual/frontend/src';

test('tool call geometry matches genuine Piclaw collapsed, tail and full states', async ({ page }, info) => {
  const source = await readFile(path.join(reference,'components/message-list/MessageItem.tsx'),'utf8');
  const start = source.indexOf('const TOOL_OUTPUT_TAIL_LINES');
  const end = source.indexOf('\n}', source.indexOf('export function ToolCallBlock',start)) + 2;
  if(start < 0 || end < start) throw new Error('Upstream tool source boundaries changed');
  const toolSource = `import {useState} from 'preact/hooks'; import {CopyButton} from ${JSON.stringify(path.join(reference,'components/CopyButton.tsx'))};\n` + source.slice(start,end);
  const result = await build({
    stdin: { contents: `import {render} from 'preact';
      import {ToolCallBlock as Reference} from 'reference-tool';
      import {ToolCallBlock as Tau} from ${JSON.stringify(path.join(frontend, 'src/components/Timeline.tsx'))};
      const output = Array.from({length:25},(_,i)=>'Output line '+(i+1)).join('\\n');
      window.renderTau = () => render(<Tau call={{id:'read',name:'read',arguments:{path:'notes.txt'}}} result={{role:'tool',content:output,toolOk:true}} />,document.getElementById('app'));
      render(<Reference useBlock={{type:'tool_use',name:'read',input:{path:'notes.txt'}}} resultBlock={{type:'tool_result',content:output}} />,document.getElementById('app'));`, loader:'tsx', resolveDir:frontend },
    alias: {
      'preact/hooks': path.join(frontend,'node_modules/preact/hooks/dist/hooks.module.js'),
      'preact/jsx-runtime': path.join(frontend,'node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js'),
      'preact': path.join(frontend,'node_modules/preact/dist/preact.module.js'),
    },
    metafile:true, bundle:true, write:false, format:'iife', jsx:'automatic', jsxImportSource:'preact',
    nodePaths:[path.join(frontend,'node_modules'), path.resolve(import.meta.dirname,'../node_modules')],
    // Release omits this non-rendering helper; fixture never changes identity/title.
    plugins:[{name:'fixture-title',setup(build){
      build.onResolve({filter:/^reference-tool$/},()=>({path:'tool',namespace:'reference'}));
      build.onLoad({filter:/.*/,namespace:'reference'},()=>({contents:toolSource,loader:'tsx',resolveDir:frontend}));
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
  await page.setContent('<meta name="viewport" content="width=device-width, initial-scale=1"><div id="app"></div>');
  expect(await page.evaluate(() => document.documentElement.clientWidth)).toBe(page.viewportSize().width);
  await page.addStyleTag({content:await readFile(path.join(frontend,'../static/piclaw-reference.css'),'utf8')});
  await page.addScriptTag({content:result.outputFiles[0].text});
  await page.addStyleTag({content:'* { transition:none!important; animation:none!important; }'});
  const measure = () => page.locator('.message-list__tool-call, .message-list__tool-call-header, .tool-call__pre-wrapper, pre, .tool-call__hidden-lines').evaluateAll(elements => elements.map(el => {
    const r=el.getBoundingClientRect(), s=getComputedStyle(el);
    return {className:el.className,width:r.width,height:r.height,text:el.textContent,font:s.font,padding:s.padding};
  }));
  const capture = async label => {
    const states = [];
    states.push(await measure());
    await page.locator('.message-list__tool-call-header').click();
    await expect(page.getByTitle('Show full output')).toBeVisible();
    states.push(await measure());
    await page.getByTitle('Show full output').click();
    await expect(page.getByRole('button',{name:'collapse',exact:true})).toBeVisible();
    states.push(await measure());
    await mkdir('/workspace/tmp/tau-tool-reference',{recursive:true});
    await page.screenshot({path:`/workspace/tmp/tau-tool-reference/${info.project.name}-${label}.png`});
    return states;
  };
  const upstream = await capture('piclaw');
  await page.evaluate(() => window.renderTau());
  const tau = await capture('tau');
  await writeFile(`/workspace/tmp/tau-tool-reference/${info.project.name}.json`,JSON.stringify({upstream,tau},null,2));
  expect(tau).toEqual(upstream);
});
