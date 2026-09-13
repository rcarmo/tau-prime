import {test,expect} from 'bun:test';
import {installTauWidgetActions} from '../static/js/tau-widget-actions.js';
test('widget actions return correlated success/errors and clean up',async()=>{
 const target=new EventTarget(),calls=[],replies=[];let reject=false;
 const dispose=installTauWidgetActions({target,renderer:{respondWidget:(...args)=>replies.push(args)},client:{extensionRequest:async(...args)=>{calls.push(args);if(reject)throw new Error('denied');return {ok:true};}}});
 const detail={frame_id:'frame',extension_id:'ext',widget_id:'widget',request_id:'request',name:'click',payload:{value:1}};
 target.dispatchEvent(new CustomEvent('tau:widget-action',{detail}));await Bun.sleep(0);
 expect(calls[0][0]).toBe('/api/extensions/widgets/ext/widget/actions/click');expect(replies[0]).toEqual(['frame','request',{result:{ok:true}}]);
 reject=true;target.dispatchEvent(new CustomEvent('tau:widget-action',{detail}));await Bun.sleep(0);expect(replies[1]).toEqual(['frame','request',{error:'denied'}]);
 dispose();target.dispatchEvent(new CustomEvent('tau:widget-action',{detail}));await Bun.sleep(0);expect(calls.length).toBe(2);
});
test('widget refresh uses identity and ignores event URL',async()=>{
 const target=new EventTarget(),calls=[],updates=[];
 const dispose=installTauWidgetActions({target,renderer:{refreshWidget:(...args)=>updates.push(args)},client:{widgetDocument:async(...args)=>{calls.push(args);return '<p>Updated</p>';}}});
 target.dispatchEvent(new CustomEvent('tau:widget-refresh',{detail:{frame_id:'ext:widget',extension_id:'ext',widget_id:'widget',url:'https://untrusted.invalid'}}));await Bun.sleep(0);
 expect(calls).toEqual([['ext','widget']]);expect(updates).toEqual([['ext:widget','<p>Updated</p>']]);dispose();
});
