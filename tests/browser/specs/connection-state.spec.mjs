import { expect, test } from '@playwright/test';

test('classic connection label is hidden only while live', async ({page})=>{
  await page.route('**/api/events*',r=>r.fulfill({contentType:'text/event-stream',body:': fixture\n\n'}));
  await page.goto('/',{waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancel=page.getByRole('button',{name:'Cancel',exact:true});
  await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});
  if(await cancel.isVisible())await cancel.click();
  await expect(page.locator('#compose-input')).toBeVisible();
  for(const [state,message] of [['live','Live'],['connecting','Reconnecting…'],['offline','Offline']]) {
    await page.evaluate(detail=>window.dispatchEvent(new CustomEvent('tau:connection-state',{detail})),{state,message});
    await expect(page.locator('#status-stream')).toHaveText(message);
    await expect(page.locator('#status-stream')).toHaveAttribute('data-state',state);
    if(state==='live') await expect(page.locator('#status-stream')).toBeHidden();
    else await expect(page.locator('#status-stream')).toBeVisible();
  }
});
