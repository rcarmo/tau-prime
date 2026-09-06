import { expect, test } from '@playwright/test';

test('branch section hides empty content and preserves selection behavior', async ({ page }) => {
  await page.route('**/api/events*',route=>route.fulfill({contentType:'text/event-stream',body:': fixture\n\n'}));
  await page.goto('/',{waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancel=page.getByRole('button',{name:'Cancel',exact:true});
  if(await cancel.isVisible()) await cancel.click();
  await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tau:branches-render',{detail:{items:[]}})));
  await expect(page.locator('#branch-list')).toBeAttached();
  await expect(page.locator('#branch-list')).toBeHidden();
  await page.evaluate(()=>{
    window.addEventListener('tau:branch-select',event=>{window.selectedBranch=event.detail.leafId;},{once:true});
    window.dispatchEvent(new CustomEvent('tau:branches-render',{detail:{items:[{leafId:'review-branch',label:'Review branch',active:true}]}}));
  });
  const branch=page.locator('#branch-list button');
  await expect(branch).toBeVisible();
  await expect(branch).toHaveAttribute('data-active','true');
  await branch.click();
  expect(await page.evaluate(()=>window.selectedBranch)).toBe('review-branch');
});
