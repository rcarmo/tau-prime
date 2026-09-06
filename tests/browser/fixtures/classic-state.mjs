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
export const tauMeters = {
  cpu_percent:10, ram_percent:25, process_rss_bytes:83886080, swap_percent:0,
  cpu_series:[10,10,10], ram_series:[25,25,25],
  process_rss_series_bytes:[83886080,83886080,83886080], swap_series:[0,0,0],
};
