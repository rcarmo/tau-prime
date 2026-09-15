import { expect, test } from '@playwright/test';

test('tool-only and long message collapse retains preview and full content', async ({ page }) => {
  await page.route('**/api/events*',r=>r.fulfill({contentType:'text/event-stream',body:': fixture\n\n'}));
  await page.goto('/',{waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancel=page.getByRole('button',{name:'Cancel',exact:true});
  await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});
  if(await cancel.isVisible()) await cancel.click();
  await expect(page.locator('#compose-input')).toBeVisible();
  const text='A long message with content. '.repeat(12);
  await page.evaluate(text=>window.dispatchEvent(new CustomEvent('tau:timeline-render',{detail:{selected:true,items:[
    {id:'long',role:'user',content:text},
    {id:'toolonly',role:'assistant',toolCalls:[{id:'read',name:'read',arguments:{path:'file'}}]},
    {id:'result',role:'tool',toolCallId:'read',content:'Tool result',toolOk:true},
  ]}})),text);
  const tool=page.locator('#post-toolonly');
  await expect(tool.getByRole('button',{name:'Copy message',exact:true})).toHaveCount(0);
  await tool.getByRole('button',{name:'Collapse message',exact:true}).focus(); await page.keyboard.press('Enter');
  await expect(tool.locator('.post-content > span')).toHaveText('— collapsed');
  await page.keyboard.press('Enter');
  await expect(tool.locator('.agent-thinking')).toBeVisible();
  const long=page.locator('#post-long');
  await long.getByRole('button',{name:'Collapse message',exact:true}).focus(); await page.keyboard.press('Enter');
  await expect(long.locator('.post-content > span')).toHaveText(text.replace(/\s+/g,' ').slice(0,120)+'…');
  await page.keyboard.press('Enter');
  await expect(long.locator('.post-content')).toHaveText(text);
});
