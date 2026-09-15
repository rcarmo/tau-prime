import { expect, test } from '@playwright/test';

test('message action copies original Markdown and announces clipboard failure', async ({ page }) => {
  await page.route('**/api/events*',r=>r.fulfill({contentType:'text/event-stream',body:': fixture\n\n'}));
  await page.goto('/',{waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancel=page.getByRole('button',{name:'Cancel',exact:true});
  if(await cancel.isVisible()) await cancel.click();
  const text='**Original** café 日本語';
  await page.evaluate(content=>{
    Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.messageCopy=text;}}});
    window.dispatchEvent(new CustomEvent('tau:timeline-render',{detail:{selected:true,items:[{id:'copy',role:'assistant',content}]}}));
  },text);
  const copy=page.getByRole('button',{name:'Copy message',exact:true});
  await copy.focus();
  await page.keyboard.press('Enter');
  expect(await page.evaluate(()=>window.messageCopy)).toBe(text);
  await expect(page.locator('.post-action-controls [role="status"]')).toHaveText('Message copied');
  await page.getByRole('button',{name:'Collapse message',exact:true}).focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#post-copy .post-content > span')).toHaveText(text);
  await expect(page.locator('#post-copy .post-content strong')).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Expand message',exact:true})).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#post-copy .post-content strong')).toHaveText('Original');
  await expect(page.getByRole('button',{name:'Collapse message',exact:true})).toBeFocused();
  await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw Error('Denied');}}}));
  await copy.focus(); await page.keyboard.press('Enter');
  await expect(page.locator('.post-action-controls [role="status"]')).toHaveText('Unable to copy message');
});
