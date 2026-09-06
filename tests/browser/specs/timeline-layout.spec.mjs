import { expect, test } from '@playwright/test';

test('timeline applies Piclaw reversed flex layout with chronological visual order', async ({ page }) => {
  await page.route('**/api/events*', r=>r.fulfill({contentType:'text/event-stream',body:': fixture\n\n'}));
  await page.goto('/',{waitUntil:'domcontentloaded'});
  await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
  const cancel=page.getByRole('button',{name:'Cancel',exact:true});
  if(await cancel.isVisible()) await cancel.click();
  await page.evaluate(()=>window.dispatchEvent(new CustomEvent('tau:timeline-render',{detail:{selected:true,items:[
    {id:'first',role:'user',content:'First message'},
    {id:'second',role:'assistant',content:'Second message'},
  ]}})));
  const list=page.locator('#timeline-list');
  await expect(list.locator(':scope > .message-list__item')).toHaveCount(2);
  const layout=await list.evaluate(el=>{
    const items=[...el.children].map(n=>({text:n.textContent,rect:n.getBoundingClientRect()}));
    const s=getComputedStyle(el);
    return {direction:s.flexDirection,gap:s.gap,items:items.map(x=>({text:x.text,top:x.rect.top,bottom:x.rect.bottom}))};
  });
  expect(layout.direction).toBe('column-reverse');
  expect(layout.gap).toBe('10px');
  expect(layout.items[0].text).toContain('Second message');
  expect(layout.items[1].text).toContain('First message');
  expect(layout.items[0].top-layout.items[1].bottom).toBeCloseTo(10,1);
});
