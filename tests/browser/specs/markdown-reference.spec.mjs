import { expect, test } from '@playwright/test';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
const frontend = path.resolve(import.meta.dirname, '../../../src/tau_web/frontend');
const require = createRequire(path.join(frontend, 'package.json'));
const { build } = require('esbuild');
const reference = process.env.PICLAW_VISUAL_SOURCE || '/opt/piclaw/releases/piclaw-2.15.3-linux-x64-baseline/app/runtime/web/static/visual/frontend/src';

test('core rich Markdown matches actual Piclaw pipeline', async ({ page }) => {
  const content = '# Review\n\n**Ready** and `code`.\n\n- First\n- Second\n\n> Keep the API.\n\n```js\nconst n = 1;\n```\n\n[Documentation](https://example.com/docs)';
  const result = await build({
    stdin: { contents: `import {render} from 'preact'; import {marked} from 'marked';
      import {renderMarkdown} from ${JSON.stringify(path.join(reference,'utils/markdown-pipeline.ts'))};
      import {MarkdownContent} from ${JSON.stringify(path.join(frontend,'src/components/MarkdownContent.tsx'))};
      window.marked = marked;
      const content = ${JSON.stringify(content)};
      render(<div className="message-list__content" dangerouslySetInnerHTML={{__html:renderMarkdown(content)}} />,document.getElementById('reference'));
      render(<MarkdownContent content={content} />,document.getElementById('tau'));`, loader:'tsx',resolveDir:frontend },
    bundle:true,write:false,format:'iife',jsx:'automatic',jsxImportSource:'preact',
    alias:{preact:path.join(frontend,'node_modules/preact')},
    nodePaths:[path.join(frontend,'node_modules')],
  });
  await page.route('http://markdown.test/**', r=>r.fulfill({contentType:'text/html',body:'<meta name="viewport" content="width=device-width, initial-scale=1"><div id="reference"></div><div id="tau"></div>'}));
  await page.goto('http://markdown.test/');
  await page.addStyleTag({content:await readFile(path.join(frontend,'../static/piclaw-reference.css'),'utf8')});
  await page.addScriptTag({content:result.outputFiles[0].text});
  const measure = selector => page.locator(selector).evaluate(root=>({
    html:root.innerHTML,
    elements:[...root.querySelectorAll('*')].map(el=>{const s=getComputedStyle(el),r=el.getBoundingClientRect();return {tag:el.tagName,width:Math.round(r.width*1000)/1000,height:Math.round(r.height*1000)/1000,font:s.font,margin:s.margin,whiteSpace:s.whiteSpace};}),
  }));
  expect(await measure('#tau')).toEqual(await measure('#reference'));
});
