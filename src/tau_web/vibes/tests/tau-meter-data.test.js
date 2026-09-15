import {test,expect} from 'bun:test';
import {meterRows,meterSparkline} from '../static/js/tau-meter-data.js';
test('meters retain unavailable values and use real histories',()=>{
 expect(meterRows()[0].value).toBe('Unavailable');
 expect(meterRows({cpu_percent:0,cpu_history:[0,100]})[0]).toEqual({kind:'cpu',label:'CPU',value:'0%',path:'M0.00,16.00 L56.00,0.00'});
 expect(meterRows({process_rss_bytes:1048576})[3].value).toBe('1.0M');
});
test('missing samples break lines rather than inventing zeroes',()=>{
 expect(meterSparkline([0,null,100])).toBe('M0.00,16.00  M56.00,0.00');
 expect(meterSparkline([])).toBe('');
 expect(meterSparkline([NaN,Infinity])).toBe(' ');
});
test('native backend series populate sparklines without fixture aliases',()=>{
 const rows=meterRows({cpu_percent:25,cpu_series:[0,25],process_rss_bytes:104857600,process_rss_series_bytes:[83886080,104857600]});
 expect(rows[0].path).toBe('M0.00,16.00 L56.00,12.00');
 expect(rows[3].path).toBe('M0.00,16.00 L56.00,0.00');
});
test('buffer cache renders native byte counter and sample range',()=>{
 const row=meterRows({buffer_cache_bytes:2147483648,buffer_cache_series_bytes:[1073741824,2147483648]}).find(row=>row.kind==='buf');
 expect(row.value).toBe('2.0G');expect(row.path).toBe('M0.00,16.00 L56.00,0.00');
});
