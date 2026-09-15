/** Render only recorded samples; missing/nonfinite samples break the sparkline. */
export function meterSparkline(history,maximum=100,minimum=0){
 if(!Array.isArray(history)||history.length<2)return '';
 const points=history.slice(-30);let pen=false;
 return points.map((value,index)=>{
  if(typeof value!=='number'||!Number.isFinite(value)||value<0){pen=false;return '';}
  const x=index*56/(points.length-1),y=maximum>minimum?16-Math.max(0,Math.min((value-minimum)/(maximum-minimum),1))*16:8;
  const command=pen?'L':'M';pen=true;return `${command}${x.toFixed(2)},${y.toFixed(2)}`;
 }).join(' ');
}
export function meterBytes(value){
 if(value===0)return '0B';
 const units=['B','K','M','G','T'];let unit=0;
 while(value>=1024&&unit<units.length-1){value/=1024;unit++;}
 return `${value.toFixed(value>=10||unit===0?0:1)}${units[unit]}`;
}
export function meterRows(snapshot={}){
 return [['cpu','CPU','cpu_percent','cpu_history'],['ram','RAM','ram_percent','ram_history'],['swap','Swap','swap_percent','swap_history'],['rss','RSS','process_rss_bytes','process_rss_history'],['buf','BUF','buffer_cache_bytes','buffer_cache_series_bytes']].map(([kind,label,key,historyKey])=>{
  const nativeHistory={cpu:'cpu_series',ram:'ram_series',swap:'swap_series',rss:'process_rss_series_bytes',buf:'buffer_cache_series_bytes'};
  const value=snapshot[key],history=snapshot[nativeHistory[kind]]??snapshot[historyKey];
  const valid=typeof value==='number'&&Number.isFinite(value)&&value>=0;
  const bytes=kind==='rss'||kind==='buf';
  const maximum=bytes?Math.max(1,...(Array.isArray(history)?history.filter(v=>typeof v==='number'&&Number.isFinite(v)&&v>=0):[])):100;
  return {kind,label,value:valid?(bytes?meterBytes(value):`${Math.round(Math.max(0,Math.min(100,value)))}%`):'Unavailable',path:meterSparkline(history,maximum,bytes&&Array.isArray(history)?Math.min(...history.filter(v=>typeof v==='number'&&Number.isFinite(v)&&v>=0)):0)};
 });
}
