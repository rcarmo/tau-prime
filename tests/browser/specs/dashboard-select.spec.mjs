import { expect, test } from '@playwright/test';

test('Dashboard session selection closes modal and releases timeline focus', async ({page,request}, info)=>{
 const id=`dashboard-select-${info.project.name}`;
 const created=await request.post('/api/sessions',{data:{session_id:id,provider_name:'test',model:'model',title:'Dashboard target'}});
 expect(created.status()).toBe(201);
 await page.route(/\/dashboard\?/,r=>r.fulfill({contentType:'application/json',body:JSON.stringify({sessions:[{session_id:id,title:'Dashboard target'}],page:1,total_pages:1})}));
 await page.goto('/',{waitUntil:'domcontentloaded'});
 await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});if(await cancel.isVisible())await cancel.click();
 await page.getByRole('button',{name:'Dashboard',exact:true}).click();
 await page.locator('.dashboard-tile-button').click();
 await expect(page.getByRole('dialog',{name:'Session dashboard'})).toBeHidden();
 await expect(page.locator('#status-session')).toHaveText('Dashboard target');
 await expect(page.locator('#timeline-main')).toBeFocused();
 expect(await page.locator('#timeline-main').evaluate(el=>Boolean(el.closest('[inert]')))).toBe(false);
});

test('declining Dashboard session switch preserves unsaved plan and modal', async ({page,request}, info)=>{
 const current=`dashboard-current-${info.project.name}`, target=`dashboard-other-${info.project.name}`;
 for(const [id,title] of [[current,'Current review'],[target,'Other review']]) {
  const response=await request.post('/api/sessions',{data:{session_id:id,provider_name:'test',model:'model',title}});
  expect(response.status()).toBe(201);
 }
 await page.route(/\/dashboard\?/,r=>r.fulfill({contentType:'application/json',body:JSON.stringify({sessions:[{session_id:target,title:'Other review'}],page:1,total_pages:1})}));
 await page.goto(`/?session_id=${current}`,{waitUntil:'domcontentloaded'});
 await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});if(await cancel.isVisible())await cancel.click();
 await expect(page.locator('#status-session')).toHaveText('Current review');
 await page.getByRole('button',{name:'Plan',exact:true}).first().click();
 await page.locator('#plan-editor').fill('- [ ] Unsaved review');
 await expect(page.locator('#plan-save-button')).toBeEnabled();
 await page.getByRole('button',{name:'Dashboard',exact:true}).click();
 const confirmation=page.waitForEvent('dialog');
 const click=page.locator('.dashboard-tile-button').click();
 const prompt=await confirmation;
 expect(prompt.type()).toBe('confirm');
 expect(prompt.message()).toContain('Discard unsaved plan edits');
 await prompt.dismiss(); await click;
 await expect(page.getByRole('dialog',{name:'Session dashboard'})).toBeVisible();
 await expect(page.locator('#status-session')).toHaveText('Current review');
 await expect(page.locator('#plan-editor')).toHaveValue('- [ ] Unsaved review');
 await page.keyboard.press('Escape');
 await expect(page.getByRole('dialog',{name:'Session dashboard'})).toBeHidden();
 await expect(page.locator('#plan-save-button')).toBeEnabled();
});
