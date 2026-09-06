import { expect, test } from '@playwright/test';

test('agent Markdown renders semantic content without active HTML', async ({ page }) => {
  await page.route('**/api/events*', r => r.fulfill({contentType:'text/event-stream',body:': fixture\n\n'}));
  await page.goto('/', {waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancel=page.getByRole('button',{name:'Cancel',exact:true});
  await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});
  if(await cancel.isVisible()) await cancel.click();
  await expect(page.locator('#compose-input')).toBeVisible();
  await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', {configurable:true,value:{writeText:async text=>{window.copiedCode=text;}}}));
  await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tau:timeline-render',{detail:{selected:true,items:[
    {id:'agent',role:'assistant',content:'# Review\n\n**Ready** and `code`.\n\n- First\n- Second\n\n```js\nconst n = 1; // café 日本語 🚀\n```\n\n[Unsafe](javascript:alert(1)) <img src="x" onerror="window.pwned=true"><script>window.pwned=true</script>'},
    {id:'user',role:'user',content:'**literal user text**'},
  ]}})));
  const content=page.locator('#post-agent .post-content');
  await expect(content.locator('h1')).toHaveText('Review');
  await expect(content.locator('strong')).toHaveText('Ready');
  await expect(content.locator('li')).toHaveCount(2);
  await expect(content.locator('pre code')).toContainText('const n = 1;');
  await expect(content.locator('script, [onerror], a[href^="javascript:"]')).toHaveCount(0);
  expect(await page.evaluate(()=>window.pwned)).toBeUndefined();
  await content.getByRole('button',{name:'Copy code',exact:true}).click();
  expect(await page.evaluate(()=>window.copiedCode)).toBe('const n = 1; // café 日本語 🚀\n');
  await expect(page.getByRole('status',{name:'Code clipboard status'})).toHaveText('Code copied');
  await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw Error('Denied');}}}));
  await content.getByRole('button',{name:'Copy code',exact:true}).click();
  await expect(page.getByRole('status',{name:'Code clipboard status'})).toHaveText('Unable to copy code; try again');
  await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.copiedCode=text;}}}));
  await content.getByRole('button',{name:'Copy code',exact:true}).click();
  await expect(page.getByRole('status',{name:'Code clipboard status'})).toHaveText('Code copied');
  await expect(page.locator('#post-user .post-content')).toHaveText('**literal user text**');
});

test('classic large code collapses, keeps toggle focus and copies complete text',async({page})=>{
 await page.goto('/');await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});if(await cancel.isVisible())await cancel.click();
 const code=Array.from({length:45},(_,i)=>`line ${i} café`).join('\n')+'\n';
 await page.evaluate(code=>{Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>window.largeCopied=text}});window.dispatchEvent(new CustomEvent('tau:timeline-render',{detail:{selected:true,items:[{id:'large',role:'assistant',content:'```txt\n'+code+'```'}]}}));},code);
 const block=page.locator('#post-large .post-code-block');
 await expect(block).toHaveClass(/post-code-block-collapsed/);
 const toggle=block.getByRole('button',{name:/Expand code/});await toggle.focus();await page.keyboard.press('Enter');
 await expect(block).toHaveClass(/post-code-block-expanded/);
 await expect(block.getByRole('button',{name:'Collapse code'})).toBeFocused();
 await page.keyboard.press('Enter');await expect(block).not.toHaveClass(/post-code-block-expanded/);
 await block.getByRole('button',{name:'Copy code',exact:true}).click();
 expect(await page.evaluate(()=>window.largeCopied)).toBe(code);
});
