import assert from 'node:assert/strict';
import { chromium, webkit } from 'playwright';
import { readFileSync } from 'node:fs';

const modulePath=process.env.SAFE_SVG_MODULE||new URL('../static/js/safe-svg.js',import.meta.url).pathname;
const moduleUrl=`data:text/javascript;base64,${Buffer.from(readFileSync(modulePath)).toString('base64')}`;
for(const [name,engine] of [['chromium',chromium],['webkit',webkit]]){
 const browser=await engine.launch({headless:true});
 try{
  const page=await browser.newPage();const external=[];
  page.on('request',request=>{if(/^https?:/.test(request.url()))external.push(request.url());});
  await page.goto('about:blank');
  const result=await page.evaluate(async url=>{
   const {sanitizeModelSvg,svgDataUrl}=await import(url);
   window.__svgExecuted=0;
   const source='<svg viewBox="0 0 20 20" onclick="window.__svgExecuted=1"><script>window.__svgExecuted=2</script><foreignObject><p>bad</p></foreignObject><rect width="20" height="20" fill="#00aa55"/><image href="https://evil.invalid/x.png"/></svg>';
   const sanitized=sanitizeModelSvg(source);const img=document.createElement('img');img.alt='Model-generated SVG';img.src=svgDataUrl(sanitized);document.body.append(img);await img.decode();
   return{sanitized,executed:window.__svgExecuted,width:img.naturalWidth,height:img.naturalHeight,alt:img.alt};
  },moduleUrl);
  assert.ok(result.sanitized.includes('<rect'));assert.ok(!/script|onclick|foreignObject|evil\.invalid/i.test(result.sanitized));assert.equal(result.executed,0);assert.ok(result.width>0);assert.ok(result.height>0);assert.ok(result.sanitized.includes('viewBox="0 0 20 20"'));assert.equal(result.alt,'Model-generated SVG');assert.deepEqual(external,[]);
  console.log(`${name}: safe inline SVG passed`);
 }finally{await browser.close();}
}
