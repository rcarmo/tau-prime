import { expect, test } from '@playwright/test';

test('connection dot and label follow the same adapter state', async ({page})=>{
  await page.route('**/api/events*',r=>r.fulfill({contentType:'text/event-stream',body:': fixture\n\n'}));
  await page.goto('/',{waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  for(const [state,message] of [['live','Live'],['connecting','Reconnecting…'],['offline','Offline']]) {
    await page.evaluate(detail=>window.dispatchEvent(new CustomEvent('tau:connection-state',{detail})),{state,message});
    await expect(page.locator('#status-stream')).toHaveText(message);
    await expect(page.locator('#status-stream')).toHaveAttribute('data-state',state);
    await expect(page.locator('.status-bar__conn-dot')).toHaveClass(new RegExp(`--${state==='live'?'connected':'disconnected'}$`));
  }
});
