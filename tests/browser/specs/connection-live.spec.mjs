import { expect, test } from '@playwright/test';

test('real SSE reports Live and changes indicator after network interruption', async ({ page, context, request }, info) => {
  const response=await request.post('/api/sessions',{data:{provider_name:'test',model:'model',title:`SSE ${info.project.name}`,session_id:`sse-${info.project.name}`}});
  expect(response.status()).toBe(201);
  const session=await response.json();
  await page.goto(`/?session_id=${session.session_id}`,{waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancel=page.getByRole('button',{name:'Cancel',exact:true});
  await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});
  if(await cancel.isVisible())await cancel.click();
  await expect(page.locator('#compose-input')).toBeVisible();
  await expect(page.locator('#status-stream')).toHaveAttribute('data-state','live');
  await expect(page.locator('#status-stream')).toBeHidden();
  await context.setOffline(true);
  try {
    await expect(page.locator('#status-stream')).toHaveAttribute('data-state',/retrying|offline|connecting/,{timeout:15000});
    await expect(page.locator('#status-stream')).toBeVisible();
  } finally { await context.setOffline(false); }
  await expect(page.locator('#status-stream')).toHaveAttribute('data-state','live',{timeout:15000});
  await expect(page.locator('#status-stream')).toBeHidden();
});
