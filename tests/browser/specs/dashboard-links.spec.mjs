import { expect, test } from '@playwright/test';

test('Dashboard only intercepts ordinary primary-link activation',async({page})=>{
 await page.route('**/dashboard*',r=>r.fulfill({contentType:'application/json',body:JSON.stringify({sessions:[{session_id:'review',title:'Review'}],page:1,total_pages:1})}));
 await page.goto('/',{waitUntil:'domcontentloaded'});
 await expect(page.locator('html')).toHaveAttribute('data-tau-shell-ready','true');
 const cancel=page.getByRole('button',{name:'Cancel',exact:true});if(await cancel.isVisible()) await cancel.click();
 await page.getByRole('button',{name:'Dashboard',exact:true}).click();
 const link=page.locator('.dashboard-tile-button');await expect(link).toHaveCount(1);
 await expect(link).toHaveAttribute('href',/session_id=review/);
 const result=await link.evaluate(el=>{
   const selections=[];
   window.addEventListener('tau:session-select',e=>{selections.push(e.detail.sessionId);e.stopImmediatePropagation();},true);
   const samples=[];
   // Observe component preventDefault, then suppress browser navigation only
   // at document bubble phase so no windows are opened by synthetic tests.
   for(const init of [{ctrlKey:true},{metaKey:true},{shiftKey:true},{altKey:true},{button:1},{}]) {
     let prevented=false;
     const observe=e=>{prevented=e.defaultPrevented;e.preventDefault();};
     document.addEventListener('click',observe,{once:true});
     el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,button:0,...init}));
     samples.push(prevented);
   }
   return {samples,selections};
 });
 expect(result.samples).toEqual([false,false,false,false,false,true]);
 expect(result.selections).toEqual(['review']);
});
