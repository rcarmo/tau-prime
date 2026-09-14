/** Render only recorded samples; missing/nonfinite samples break the sparkline. */
export function meterSparkline(history,maximum=100){
 if(!Array.isArray(history)||history.length<2)return '';
 const points=history.slice(-30);let pen=false;
 return points.map((value,index)=>{
  if(typeof value!=='number'||!Number.isFinite(value)||value<0){pen=false;return '';}
  const x=index*56/(points.length-1),y=15-Math.min(value/Math.max(maximum,1),1)*14;
  const command=pen?'L':'M';pen=true;return `${command}${x.toFixed(2)},${y.toFixed(2)}`;
 }).join(' ');
}
export function meterRows(snapshot={}){
 return [['cpu','CPU','cpu_percent','cpu_history'],['ram','RAM','ram_percent','ram_history'],['swap','Swap','swap_percent','swap_history'],['rss','RSS','process_rss_bytes','process_rss_history']].map(([kind,label,key,historyKey])=>{
  const value=snapshot[key],history=snapshot[historyKey];
  const valid=typeof value==='number'&&Number.isFinite(value)&&value>=0;
  const maximum=kind==='rss'?Math.max(1,...(Array.isArray(history)?history.filter(v=>typeof v==='number'&&Number.isFinite(v)&&v>=0):[])):100;
  return {kind,label,value:valid?(kind==='rss'?`${(value/1048576).toFixed(1)} MiB`:`${value.toFixed(1)}%`):'Unavailable',path:meterSparkline(history,maximum)};
 });
}
