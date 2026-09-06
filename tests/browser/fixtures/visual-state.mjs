// Visible content shared by genuine Piclaw and Tau full-shell capture adapters.
export const modelName = 'review-model';
export const providerName = 'test';
export const fixedTime = '2026-09-01T12:02:00Z';
export const userText = 'Review the workspace and preserve the existing API.';
export const agentText = '## Workspace review\n\nThe API is **unchanged**.\n\n- Routes retained\n- Streaming retained\n\n```ts\nconst ready = true;\n```';
export const toolOutput = '# Workspace\nThis is the deterministic review fixture.';
export const tauItems = [
  {id:'user',role:'user',content:userText,meta:'2m ago'},
  {id:'agent',role:'assistant',content:agentText,meta:'1m ago',toolCalls:[{id:'read',name:'read',arguments:{path:'README.md'}}]},
  {id:'result',role:'tool',toolCallId:'read',content:toolOutput,toolOk:true},
];
export const piclawPosts = [
  {id:2,type:'agent',content:agentText,created_at:'2026-09-01T12:01:00Z',content_blocks:[
    {type:'tool_use',id:'read',name:'read',input:{path:'README.md'}},
    {type:'tool_result',tool_use_id:'read',content:toolOutput},
  ]},
  {id:1,type:'user',content:userText,created_at:'2026-09-01T12:00:00Z'},
];
export const tauMeters = {
  cpu_percent:10, ram_percent:25, process_rss_bytes:83886080, swap_percent:0,
  cpu_series:[10,10,10], ram_series:[25,25,25],
  process_rss_series_bytes:[83886080,83886080,83886080], swap_series:[0,0,0],
};
export const piclawMeters = {
  cpu_percent:tauMeters.cpu_percent, ram_percent:tauMeters.ram_percent,
  swap_percent:tauMeters.swap_percent, buffer_cache_bytes:1048576,
  vram_percent:null, gpu_provider:null,
  process_memory:{rss_bytes:tauMeters.process_rss_bytes},
};
