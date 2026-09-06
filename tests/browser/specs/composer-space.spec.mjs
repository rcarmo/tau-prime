import { expect, test } from '@playwright/test';

for (const colorScheme of ['light','dark']) {
test(`${colorScheme} composer controls leave text unobstructed and wrap context`, async ({ page }) => {
  await page.emulateMedia({colorScheme});
  await page.goto('/', {waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancel=page.getByRole('button',{name:'Cancel',exact:true});
  if(await cancel.isVisible()) await cancel.click();
  await page.locator('#compose-input').fill('Review this workspace and preserve API behavior.');
  const geometry=await page.evaluate(()=>{
    const input=document.querySelector('#compose-input'), toolbar=document.querySelector('.chat__toolbar');
    const r=input.getBoundingClientRect(), t=toolbar.getBoundingClientRect(), s=getComputedStyle(input);
    const textTop=r.top+parseFloat(s.paddingTop), textLeft=r.left+parseFloat(s.paddingLeft);
    return {textTop,textBottom:textTop+parseFloat(s.lineHeight),textLeft,toolbar:{left:t.left,top:t.top,bottom:t.bottom,width:t.width},inputWidth:r.width};
  });
  await page.locator('#compose-context-readout').evaluate(el => { el.textContent = 'Context 128000 / 200000 tokens · Provider example/long-model-name · Pending attachments 12'; });
  const bounds = await page.locator('.chat__compose-toolbar').evaluate(el => {
    const r=el.getBoundingClientRect();
    return {left:r.left,right:r.right,scroll:el.scrollWidth,client:el.clientWidth,viewport:innerWidth};
  });
  expect(bounds.left).toBeGreaterThanOrEqual(0);
  expect(bounds.right).toBeLessThanOrEqual(bounds.viewport);
  expect(bounds.scroll-bounds.client).toBeLessThanOrEqual(1);
  await expect(page.locator('#compose-submit')).toBeVisible();
  // Floating icons may occupy the far right, but not the first half of a text line.
  const intersects=geometry.toolbar.top < geometry.textBottom && geometry.toolbar.bottom > geometry.textTop;
  if(intersects) expect(geometry.toolbar.left-geometry.textLeft).toBeGreaterThan(geometry.inputWidth/2);
});
}
