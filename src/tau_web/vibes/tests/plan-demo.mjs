import {chromium,webkit} from 'playwright';
import {readFileSync} from 'node:fs';
const line=readFileSync('/home/agent/.tau/web-demo.env','utf8').split('\n').find(line=>line.startsWith('TAU_WEB_AUTH_TOKEN='));
const token=line?.slice(line.indexOf('=')+1).replace(/^["']|["']$/g,'');
if(!token)throw new Error('Demo token missing');
for(const engine of [chromium,webkit]){
 const browser=await engine.launch();try{
  const page=await browser.newPage({viewport:{width:1440,height:900}});
  await page.addInitScript(token=>localStorage.setItem('tau.web.authToken',token),token);
  await page.goto('http://127.0.0.1:8895/?session=d690784535ab47179a79ae53fed2cb2a');
  await page.getByRole('button',{name:'Open plan sidebar',exact:true}).click();
  await page.locator('.plan-sidebar-editor .cm-content').waitFor();
  await page.waitForFunction(()=>document.querySelector('.plan-sidebar-actions button:last-child')?.disabled===false);
  await page.waitForFunction(()=>document.querySelector('.system-meters-row.rss .system-meters-value')?.textContent.includes('MiB'));
  await page.waitForTimeout(250);
  await page.screenshot({path:`/workspace/tmp/tau-demo-evidence/${engine.name()}-desktop.png`});
  await page.getByRole('button',{name:'Close plan sidebar',exact:true}).click();
  for(const size of [{width:1440,height:900},{width:390,height:844}]){
   await page.setViewportSize(size);
   if(size.width<1024){const hide=page.getByRole('button',{name:'Hide workspace',exact:true});if(await hide.isVisible())await hide.click();}
   const meter=page.getByRole('button',{name:'Collapse system meters',exact:true});
   await meter.click();await page.getByRole('button',{name:'Expand system meters',exact:true}).click();
   if(size.width<=600)await page.locator('.system-meters-compact-summary').waitFor();
   await page.getByRole('button',{name:'Open plan sidebar',exact:true}).click();
   await page.waitForFunction(width=>document.querySelector('.plan-sidebar-panel').getBoundingClientRect().right<=width+1,size.width);
   await page.screenshot({path:`/workspace/tmp/tau-demo-evidence/${engine.name()}-${size.width}-plan.png`});
   await page.getByRole('button',{name:'Close plan sidebar',exact:true}).click();
  }
  console.log(`${engine.name()}: deployed authenticated sidebar/editor, live RSS and desktop/phone HUD toggle passed`);
 }finally{await browser.close();}
}
