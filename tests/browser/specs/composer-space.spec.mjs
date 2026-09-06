import { expect, test } from '@playwright/test';
import { installSelectedSession } from '../fixtures/selected-session.mjs';
import { installLiveStream } from '../fixtures/live-stream.mjs';

for (const colorScheme of ['light', 'dark']) test(`${colorScheme} classic composer separates session, input and actions`, async ({page}) => {
  await installSelectedSession(page); await installLiveStream(page,'tau');
  await page.emulateMedia({colorScheme});
  await page.goto('/',{waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancel=page.getByRole('button',{name:'Cancel',exact:true});
  await cancel.waitFor({state:'visible',timeout:2000}).catch(()=>{});
  if(await cancel.isVisible()) await cancel.click();
  await page.locator('#compose-input').fill('Review this workspace and preserve API behavior.');
  await page.evaluate(()=>document.getElementById('compose-context-readout').textContent='Context '.repeat(100));
  await expect(page.locator('#compose-context-readout')).toBeHidden();
  await expect(page.locator('#compose-delivery-mode')).toBeHidden();
  const input=await page.locator('#compose-input').boundingBox();
  const session=await page.locator('.compose-session-trigger-top').boundingBox();
  const footer=await page.locator('.compose-footer').boundingBox();
  // Classic overlays the session pill at top right; textarea padding reserves its space.
  const padding=await page.locator('#compose-input').evaluate(el=>({right:parseFloat(getComputedStyle(el).paddingRight),top:parseFloat(getComputedStyle(el).paddingTop)}));
  expect(input.x+input.width-padding.right <= session.x+1 || input.y+padding.top >= session.y+session.height-1).toBe(true);
  expect(footer.y).toBeGreaterThanOrEqual(input.y+input.height-1);
  for(const selector of ['#compose-input','#compose-submit','#compose-attachment-button']) {
    await expect(page.locator(selector)).toBeVisible();
    const box=await page.locator(selector).boundingBox();
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.x+box.width).toBeLessThanOrEqual(page.viewportSize().width+1);
    expect(box.y+box.height).toBeLessThanOrEqual(page.viewportSize().height+1);
  }
});
