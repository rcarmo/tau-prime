import {test,expect} from 'bun:test';
import {meterRows,meterSparkline} from '../static/js/tau-meter-data.js';
test('meters retain unavailable values and use real histories',()=>{
 expect(meterRows()[0].value).toBe('Unavailable');
 expect(meterRows({cpu_percent:0,cpu_history:[0,100]})[0]).toEqual({kind:'cpu',label:'CPU',value:'0.0%',path:'M0.00,15.00 L56.00,1.00'});
 expect(meterRows({process_rss_bytes:1048576})[3].value).toBe('1.0 MiB');
});
test('missing samples break lines rather than inventing zeroes',()=>{
 expect(meterSparkline([0,null,100])).toBe('M0.00,15.00  M56.00,1.00');
 expect(meterSparkline([])).toBe('');
 expect(meterSparkline([NaN,Infinity])).toBe(' ');
});
