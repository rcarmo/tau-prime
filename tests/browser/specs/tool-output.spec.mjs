import { expect, test } from '@playwright/test';

test('tool output shows tail, expands, collapses and copies full output', async ({ page }) => {
  await page.route('**/api/events*', route => route.fulfill({contentType:'text/event-stream',body:': fixture\n\n'}));
  await page.goto('/', {waitUntil:'domcontentloaded'});
  await expect(page.locator('#compose-input')).toBeAttached();
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready', 'true');
  const cancel = page.getByRole('button',{name:'Cancel',exact:true});
  await cancel.waitFor({state:'visible',timeout:2000}).catch(() => {});
  if (await cancel.isVisible()) await cancel.click();
  await expect(page.locator('#compose-input')).toBeVisible();
  const content = Array.from({length:25},(_,i)=>`Output line ${i+1}`).join('\n');
  await page.evaluate(content => {
    Object.defineProperty(navigator, 'clipboard', {configurable:true,value:{writeText:async text => { window.copiedOutput=text; }}});
    window.dispatchEvent(new CustomEvent('tau:timeline-render',{detail:{selected:true,items:[
      {id:'agent',role:'assistant',toolCalls:[{id:'read',name:'read',arguments:{path:'file'}}]},
      {id:'result',role:'tool',toolCallId:'read',content,toolOk:true},
    ]}}));
  },content);
  const tool = page.locator('.message-list__tool-call');
  await tool.locator('.message-list__tool-call-header').click();
  await expect(tool.locator('.tool-call__hidden-lines')).toHaveText('5 lines hidden — click to expand');
  await expect(tool.locator('pre').last()).toHaveText(content.split('\n').slice(-20).join('\n'));
  await tool.getByRole('button',{name:'Copy',exact:true}).last().click();
  expect(await page.evaluate(()=>window.copiedOutput)).toBe(content);
  await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('Denied');}}}));
  await tool.getByRole('button',{name:'Copied!',exact:true}).click();
  await expect(tool.getByRole('button',{name:'Copy failed — retry',exact:true})).toBeVisible();
  await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.copiedOutput=text;}}}));
  await tool.getByRole('button',{name:'Copy failed — retry',exact:true}).click();
  await expect(tool.getByRole('button',{name:'Copied!',exact:true})).toBeVisible();
  expect(await page.evaluate(()=>window.copiedOutput)).toBe(content);
  await tool.getByTitle('Show full output').click();
  await expect(tool.locator('pre').last()).toHaveText(content);
  await tool.getByRole('button',{name:'collapse',exact:true}).click();
  await expect(tool.getByTitle('Show full output')).toBeVisible();
});
