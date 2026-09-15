import {test,expect} from 'bun:test';
import {ComposeDrafts,draftKey} from '../static/js/components/compose-drafts.js';
import {preserveQueuedRecovery,recoverQueuedDraft} from '../static/js/tau-queue-return.js';
function fixture(){
 const data=new Map();let failCleanup=false;
 const storage={getItem:key=>data.get(key)??null,setItem:(key,value)=>data.set(key,value),removeItem:key=>{if(failCleanup)throw new Error('cleanup failed');data.delete(key);}};
 return {data,storage,drafts:new ComposeDrafts(storage),fail:value=>{failCleanup=value;}};
}
test('draft saves retain applied recovery markers across intervening edits',()=>{
 const f=fixture();const key=preserveQueuedRecovery(f.storage,{sessionId:'one',queueId:'q',text:'queued'});
 f.fail(true);expect(()=>recoverQueuedDraft(f.storage,key,'one')).toThrow('cleanup failed');
 f.drafts.save('one',{text:'queued plus newer edit',fileRefs:['README.md']});
 expect(JSON.parse(f.data.get(draftKey('one'))).queueRecoveries).toEqual([key]);
 f.fail(false);expect(recoverQueuedDraft(f.storage,key,'one')).toBe('queued plus newer edit');
 expect(f.drafts.load('one').fileRefs).toEqual(['README.md']);
 f.drafts.save('one',{...f.drafts.load('one')});
 expect(JSON.parse(f.data.get(draftKey('one'))).queueRecoveries).toBeUndefined();
});
test('drafts keep page-local files and session data isolated',()=>{
 const f=fixture(),file={name:'attachment.txt'};
 f.drafts.save('one',{text:'first',files:[file],messageRefs:['12']});
 f.drafts.save('two',{text:'second'});
 expect(f.drafts.load('one')).toEqual({text:'first',files:[file],fileRefs:[],folderRefs:[],messageRefs:['12']});
 expect(f.drafts.load('two').text).toBe('second');
 expect(f.data.get(draftKey('one'))).not.toContain('attachment.txt');
});

test('model hint opacity keeps light-theme contrast above 4.5:1', async () => {
 const css=await Bun.file(new URL('../static/css/classic/base.css',import.meta.url)).text();
 const opacity=Number(css.match(/--model-hint-opacity:\s*([\d.]+)/)?.[1]);
 const linear=value=>{value/=255;return value<=0.04045?value/12.92:((value+0.055)/1.055)**2.4;};
 const luminance=rgb=>rgb.map(linear).reduce((sum,value,index)=>sum+value*[0.2126,0.7152,0.0722][index],0);
 const blended=[83,100,113].map(value=>Math.round(value*opacity+255*(1-opacity)));
 const ratio=(luminance([255,255,255])+0.05)/(luminance(blended)+0.05);
 expect(ratio).toBeGreaterThanOrEqual(4.5);
});
