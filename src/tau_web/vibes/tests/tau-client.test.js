import { test, expect } from 'bun:test';
import { createTauClient, sessionFromTau } from '../static/js/tau-client.js';
const session = {session_id:'one',title:'Example',provider_name:'provider',model:'model'};
test('session identity is explicit, never synthetic default', () => {
    expect(sessionFromTau(session).id).toBe('one');
    expect(() => sessionFromTau({})).toThrow();
});
test('list translates resources and forwards auth', async () => {
    let call;
    const client=createTauClient({getToken:()=> 'fixture',fetchImpl:async (...args)=>{call=args;return Response.json({sessions:[session]});}});
    expect((await client.sessions()).sessions[0].name).toBe('Example');
    expect(call[0]).toBe('/api/sessions?include_archived=false');
    expect(call[1].headers.Authorization).toBe('Bearer fixture');
});
test('creation fails before transport without actual provider/model', async () => {
    const client=createTauClient({fetchImpl:()=>{throw new Error('must not fetch');}});
    await expect(client.createSession({name:'new'})).rejects.toThrow('Choose a provider');
});
test('HTTP failures preserve status', async () => {
    const client=createTauClient({fetchImpl:async()=>Response.json({error:'denied'},{status:403})});
    try { await client.sessions(); throw new Error('unexpected success'); }
    catch(error) { expect(error.status).toBe(403); expect(error.message).toBe('denied'); }
});
test('catalogue deduplicates observed pairs and retains current model without invented capabilities', async () => {
    const client=createTauClient({fetchImpl:async path=>Response.json(path==='/api/models'
        ? {source:'sessions',models:[{provider_name:'provider',model:'model'}]}
        : {...session,updated_at:'r1'})});
    const result=await client.models('one');
    expect(result.models).toEqual([{id:'model',provider:'provider',name:'model',reasoning:false,contextWindow:null,thinkingLevels:[]}]);
    expect(result.source).toBe('sessions');
    expect(result.thinking_levels).toEqual([]);
});
test('model change uses displayed revision and propagates conflict without retry', async () => {
    const calls=[];
    const client=createTauClient({fetchImpl:async (path,options)=>{
        calls.push({path,...options});
        return options.method==='PATCH' ? Response.json({error:'conflict'},{status:409}) : Response.json({...session,updated_at:'r1'});
    }});
    await client.modelState('one');
    try { await client.changeModel('one',{provider:'new',model_id:'other'}); throw new Error('unexpected success'); }
    catch(error) { expect(error.status).toBe(409); }
    expect(calls.length).toBe(2);
    expect(JSON.parse(calls[1].body)).toEqual({provider_name:'new',model:'other',expected_updated_at:'r1'});
});
test('timeline translates forward pages into newest-first older pages', async()=> {
    const records=Array.from({length:205},(_,i)=>({message_id:i+1,session_id:'one',role:'assistant',content:`text ${i+1}`,created_at:'2026-09-13T00:00:00Z'}));
    const client=createTauClient({fetchImpl:async path=> {
        const after=Number(new URL(path,'http://localhost').searchParams.get('after'));
        return Response.json({timeline:records.filter(r=>r.message_id>after).slice(0,200)});
    }});
    const first=await client.timeline('one',5);
    expect(first.posts.map(p=>p.id)).toEqual([205,204,203,202,201]);
    expect(first.posts[0].data.type).toBe('agent_response');
    expect(first.has_more).toBe(true);
    const second=await client.timeline('one',5,201);
    expect(second.posts.map(p=>p.id)).toEqual([200,199,198,197,196]);
    expect((await client.timeline('one',5,4)).has_more).toBe(false);
});
test('timeline rejects nonadvancing cursors', async()=> {
    const client=createTauClient({fetchImpl:async()=>Response.json({timeline:[{message_id:0}]})});
    await expect(client.timeline('one')).rejects.toThrow('cursor');
});
test('idle auto submission creates a durable run; busy submission queues follow-up', async()=> {
    for (const busy of [false,true]) {
        const calls=[];
        const client=createTauClient({fetchImpl:async(path,options)=> {
            calls.push({path,...options});
            return Response.json(options.method==='GET' ? {runs:busy?[{status:'running'}]:[]} : {run_id:'run',queue_id:7});
        }});
        const result=await client.send('one','hello');
        expect(result.accepted).toBe(true);
        expect(calls[1].path).toBe(`/api/sessions/one/${busy?'queue':'runs'}`);
        expect(JSON.parse(calls[1].body)).toEqual(busy?{content:'hello',kind:'follow_up'}:{content:'hello'});
    }
});
test('unsupported attachments and commands fail before transport; rejection is not acceptance', async()=> {
    const client=createTauClient({fetchImpl:async()=>Response.json({error:'rejected'},{status:409})});
    await expect(client.send('one','hello',{mediaIds:[1]})).rejects.toThrow('attachment');
    await expect(client.send('one','/compact')).rejects.toThrow('command');
    await expect(client.send('one','hello',{mode:'steer'})).rejects.toThrow('rejected');
});
test('model command resolves through the authoritative session mutation path',async()=>{
 const calls=[];const client=createTauClient({fetchImpl:async(path,options={})=>{calls.push({path,...options});return Response.json(options.method==='PATCH'?{provider_name:'provider',model:'model',updated_at:'r2'}:{provider_name:'old',model:'old',updated_at:'r1'});}});
 expect(await client.send('one','/model provider/model')).toEqual({accepted:true,command:'model',model:{provider:'provider',id:'model',name:'model'}});
 expect(calls.map(call=>call.path)).toEqual(['/api/sessions/one','/api/sessions/one/model']);
 expect(JSON.parse(calls[1].body)).toEqual({provider_name:'provider',model:'model',expected_updated_at:'r1'});
});
test('run status excludes finished runs; queue preserves FIFO and marks unsupported actions',async()=>{
 const client=createTauClient({fetchImpl:async path=>Response.json(path.endsWith('/runs')
 ? {runs:[{run_id:'active',session_id:'one',status:'running'},{run_id:'done',status:'completed'}]}
 : {queue:[{queue_id:8,session_id:'one',queue_kind:'follow_up',position:0,content:'next'}]})});
 expect((await client.status('one')).active_turns.map(t=>t.turn_id)).toEqual(['active']);
 const item=(await client.queue('one')).items[0];
 expect(item.row_id).toBe(8);expect(item.content).toBe('next');expect(item.tau_readonly).toBe(true);
});
test('context maps structural counts without fabricating tokens, cost or occupancy',async()=>{
 const client=createTauClient({fetchImpl:async()=>Response.json({entry_count:9,message_count:4,compaction_count:1,active_leaf_entry_id:'leaf'})});
 const context=await client.context('one');
 expect(context).toEqual({entryCount:9,messageCount:4,compactionCount:1,activeLeafEntryId:'leaf'});
 expect(context.percent).toBeUndefined();expect(context.tokens).toBeUndefined();
});
test('session creation uses saved onboarding defaults, never catalogue guesses',async()=>{
 const calls=[];
 const client=createTauClient({fetchImpl:async(path,options)=>{
  calls.push({path,...options});
  return Response.json(path==='/api/onboarding'?{default_provider:'configured',default_model:'chosen'}:{...session,provider_name:'configured',model:'chosen'});
 }});
 await client.createSession({name:'New session',useConfiguredDefaults:true});
 expect(calls.map(c=>c.path)).toEqual(['/api/onboarding','/api/sessions']);
 expect(JSON.parse(calls[1].body)).toEqual({title:'New session',provider_name:'configured',model:'chosen'});
});
test('unconfigured onboarding never submits a session',async()=>{
 const calls=[];const client=createTauClient({fetchImpl:async path=>{calls.push(path);return Response.json({default_provider:null,default_model:null});}});
 await expect(client.createSession({name:'new',useConfiguredDefaults:true})).rejects.toThrow('provider setup');
 expect(calls).toEqual(['/api/onboarding']);
});
test('archive uses Tau soft-delete route and restore uses POST',async()=>{
 const calls=[];const client=createTauClient({fetchImpl:async(path,options)=>{calls.push({path,...options});return Response.json({...session,archived_at:options.method==='DELETE'?'now':null});}});
 expect((await client.archiveSession('one',true)).session.archived).toBe(true);
 expect((await client.archiveSession('one',false)).session.archived).toBe(false);
 expect(calls.map(c=>[c.path,c.method])).toEqual([['/api/sessions/one','DELETE'],['/api/sessions/one/restore','POST']]);
});
test('workspace tree projects directories with bounded recursion and hidden filtering',async()=>{
 const calls=[];const client=createTauClient({fetchImpl:async path=>{
 calls.push(path);return Response.json({kind:'directory',entries:path==='/api/files?path=' ? [{name:'docs',path:'docs',kind:'directory'},{name:'.secret',path:'.secret',kind:'file'},{name:'link',path:'link',kind:'symlink'}] : [{name:'readme.txt',path:'docs/readme.txt',kind:'file'}]});
 }});
 const tree=await client.workspaceTree();
 expect(tree.root.children.map(n=>n.name)).toEqual(['docs']);
 expect(tree.root.children[0].children[0].type).toBe('file');
 expect(calls).toEqual(['/api/files?path=','/api/files?path=docs']);
});
test('text preview is bounded and never fabricates writable support',async()=>{
 const client=createTauClient({fetchImpl:async()=>Response.json({kind:'file',path:'file.txt',content:'abc日本',size_bytes:9})});
 const result=await client.workspaceFile('file.txt',5);
 expect(result.text).toBe('abc');expect(result.truncated).toBe(true);expect(result.read_only).toBe(true);expect(result.content_type).toBe('text/plain');
});
test('search keeps entity/session identity without invented post timestamps',async()=>{
 let path;const client=createTauClient({fetchImpl:async url=>{path=url;return Response.json({results:[{entity_type:'message',entity_id:'42',session_id:'one',text:'matched text',rank:1}]});}});
 const result=await client.search('matched',20,0,{sessionId:'one'});
 expect(path).toBe('/api/search?q=matched&limit=20&session_id=one');
 expect(result.results[0].data.entity_id).toBe('42');expect(result.results[0].timestamp).toBe(null);
 await expect(client.search('x',20,0,{images:true})).rejects.toThrow('not supported');
});
test('plan save sends caller revision and exposes current plan on conflict without retry',async()=>{
 const calls=[];const current={revision:3,markdown:'- [ ] remote'};
 const client=createTauClient({fetchImpl:async(path,options)=>{calls.push({path,...options});return Response.json({error:'Plan changed',code:'plan_revision_conflict',plan:current},{status:409});}});
 const draft='- [ ] local';
 try{await client.savePlan('one',draft,2);throw new Error('unexpected success');}
 catch(error){expect(error.status).toBe(409);expect(error.code).toBe('plan_revision_conflict');expect(error.currentPlan).toEqual(current);}
 expect(calls.length).toBe(1);expect(JSON.parse(calls[0].body)).toEqual({markdown:draft,expected_revision:2});
 expect(calls[0].headers['X-Tau-CSRF']).toBe('1');
});
test('approval reads forward cancellation for session-change and unmount cleanup',async()=>{
 const controller=new AbortController();let received;
 const client=createTauClient({fetchImpl:async(_path,options)=>{received=options.signal;return Response.json({approvals:[]});}});
 expect(await client.approvals('one',{signal:controller.signal})).toEqual([]);
 expect(received).toBe(controller.signal);
});
test('approval decisions are explicit, authenticated mutations and reject invalid choices',async()=>{
 const calls=[];const client=createTauClient({fetchImpl:async(path,options)=>{calls.push({path,...options});return Response.json({approval_id:'a',decision:'deny'});}});
 await client.resolveApproval('a','deny');
 expect(calls[0].path).toBe('/api/approvals/a');expect(JSON.parse(calls[0].body)).toEqual({decision:'deny'});expect(calls[0].headers['X-Tau-CSRF']).toBe('1');
 await expect(client.resolveApproval('a','maybe')).rejects.toThrow('Invalid');expect(calls.length).toBe(1);
});
test('media upload is session-scoped with CSRF and send uses explicit references',async()=>{
 const calls=[];const client=createTauClient({getToken:()=> 'fixture',fetchImpl:async(path,options)=>{calls.push({path,...options});return Response.json(path==='/api/media'?{media_id:'media-one'}:path.endsWith('/runs')&&options.method==='GET'?{runs:[]}:{run_id:'run'});}});
 const file=new File(['hello'],'note.txt',{type:'text/plain'});
 expect((await client.upload(file,{sessionId:'one'})).id).toBe('media-one');
 expect(calls[0].body.get('session_id')).toBe('one');expect(calls[0].headers.Authorization).toBe('Bearer fixture');
 await client.send('one','inspect',{mediaIds:['media-one']});
 expect(JSON.parse(calls.at(-1).body).content).toContain('[media:media-one]');
});
test('persisted tool metadata survives projection and malformed payload keeps text',async()=>{
 const {postFromTau}=await import('../static/js/tau-client.js');
 const post=postFromTau({message_id:1,role:'assistant',content:'',content_blocks_json:JSON.stringify({tool_calls:[{id:'call',name:'bash',arguments:{command:'echo hi'}}]})});
 expect(post.data.tau_tool_calls[0].name).toBe('bash');
 expect(postFromTau({role:'tool',content:'failure',content_blocks_json:JSON.stringify({name:'bash',tool_call_id:'call',ok:false})}).data.tau_tool_result.ok).toBe(false);
 expect(postFromTau({content:'readable',content_blocks_json:'broken'}).data.content).toBe('readable');
});
test('thinking policy uses dedicated endpoint and loaded revision without asserting reasoning support',async()=>{
 const calls=[];const client=createTauClient({fetchImpl:async(path,options)=>{calls.push({path,...options});return Response.json({...session,updated_at:'r1',thinking_level:'high'});}});
 await client.modelState('one');const state=await client.changeModel('one',{thinking_level:'high'});
 expect(calls[1].path).toBe('/api/sessions/one/thinking');expect(JSON.parse(calls[1].body)).toEqual({thinking_level:'high',expected_updated_at:'r1'});
 expect(state.model.reasoning).toBeUndefined();expect(state.thinking_level).toBe('high');
});
test('agent display identity uses actual Tau settings without invented capabilities',async()=>{
 const client=createTauClient({fetchImpl:async path=>{expect(path).toBe('/api/settings');return Response.json({agent_name:'Tau configured'});}});
 expect(await client.agentIdentity()).toEqual({agents:[{id:'default',name:'Tau configured',avatar_url:'/static/icon-192.png'}],user:{name:'You',avatar_url:null}});
});
test('persisted outcome metadata is normalized for timeline chips',async()=>{
 const {postFromTau}=await import('../static/js/tau-client.js');
 expect(postFromTau({role:'assistant',content_blocks_json:{outcome:' completed '}}).data.tau_outcome).toBe('completed');
 expect(postFromTau({role:'assistant',content_blocks_json:{outcome:''}}).data.tau_outcome).toBe(null);
});
test('persisted attachments retain stable media metadata only',async()=>{
 const {postFromTau}=await import('../static/js/tau-client.js');
 const attachment={media_id:'media',filename:'picture.png',media_type:'image/png'};
 const post=postFromTau({content_blocks_json:JSON.stringify({attachments:[attachment,null,{}]})});
 expect(post.data.tau_attachments).toEqual([attachment]);
});
test('media buffering rejects oversized declared and streamed bodies',async()=>{
 for(const declared of [true,false]){
  let cancelled=false;
  const client=createTauClient({fetchImpl:async()=>new Response(new ReadableStream({start(c){if(!declared)c.enqueue(new Uint8Array(32*1024*1024+1));},cancel(){cancelled=true;}}),{headers:declared?{'Content-Length':String(32*1024*1024+1)}:{}})});
  await expect(client.mediaBlob('large')).rejects.toThrow('32 MiB');expect(cancelled).toBe(true);
 }
});
test('bounded media reader preserves bytes and content type',async()=>{
 const client=createTauClient({fetchImpl:async()=>new Response('café',{headers:{'Content-Type':'text/plain'}})});
 const blob=await client.mediaBlob('small');expect(blob.type).toStartWith('text/plain');expect(await blob.text()).toBe('café');
});
test('branch selection submits explicit leaf rather than creating a child session',async()=>{
 const calls=[];const client=createTauClient({fetchImpl:async(path,options)=>{calls.push({path,...options});return Response.json({leaf_entry_id:'leaf'});}});
 await client.selectBranch('one','leaf');expect(calls[0].path).toBe('/api/sessions/one/branches/select');expect(JSON.parse(calls[0].body)).toEqual({leaf_entry_id:'leaf'});
 await expect(client.selectBranch('one','')).rejects.toThrow('valid conversation leaf');
});
test('extension requests stay inside Tau API and retain authentication',async()=>{
 const calls=[];const client=createTauClient({getToken:()=> 'fixture',fetchImpl:async(path,options)=>{calls.push({path,...options});return Response.json({modules:[]});}});
 expect(await client.frontendModules()).toEqual([]);
 await client.extensionRequest('/api/settings');expect(calls[1].path).toBe('/api/settings');expect(calls[1].headers.Authorization).toBe('Bearer fixture');
 for(const path of ['https://outside/api/x','//outside/api/x','/api/../outside','/outside'])await expect(client.extensionRequest(path)).rejects.toThrow('Invalid');
});
test('widget document enforces streamed size limit and cancels response',async()=>{
 let cancelled=false;
 const client=createTauClient({fetchImpl:async()=>new Response(new ReadableStream({start(c){c.enqueue(new Uint8Array(2*1024*1024+1));},cancel(){cancelled=true;}}))});
 await expect(client.widgetDocument('ext','widget')).rejects.toThrow('2 MiB');expect(cancelled).toBe(true);
});

test('widget declared oversize cancels without consuming response',async()=>{
 let cancelled=false;
 const client=createTauClient({fetchImpl:async()=>new Response(new ReadableStream({cancel(){cancelled=true;}}),{headers:{'Content-Length':String(2*1024*1024+1)}})});
 await expect(client.widgetDocument('ext','widget')).rejects.toThrow('2 MiB');
 expect(cancelled).toBe(true);
});

test('widget document preserves UTF-8 split across response chunks at exact limit',async()=>{
 const text='x'.repeat(2*1024*1024-6)+'日本';
 const bytes=new TextEncoder().encode(text);
 const client=createTauClient({fetchImpl:async()=>new Response(new ReadableStream({start(c){c.enqueue(bytes.slice(0,bytes.length-4));c.enqueue(bytes.slice(bytes.length-4));c.close();}}))});
 expect(await client.widgetDocument('ext','widget')).toBe(text);
});

test('widget truncated stream propagates read failure',async()=>{
 const client=createTauClient({fetchImpl:async()=>new Response(new ReadableStream({start(c){c.enqueue(new TextEncoder().encode('<html>'));c.error(new Error('Fixture connection reset'));}}))});
 await expect(client.widgetDocument('ext','widget')).rejects.toThrow('Fixture connection reset');
});
test('assistant posts use the configured default agent identity',async()=>{
 const {postFromTau}=await import('../static/js/tau-client.js');
 expect(postFromTau({role:'assistant',content:'reply'}).data.agent_id).toBe('default');
 expect(postFromTau({role:'user',content:'request'}).data.agent_id).toBeUndefined();
});
test('queue removal uses session-scoped Tau DELETE with CSRF',async()=>{
 const calls=[];const client=createTauClient({fetchImpl:async(path,options)=>{calls.push({path,...options});return Response.json({queue_id:'q'});}});
 await client.removeQueueItem('one','q');
 expect(calls[0].path).toBe('/api/sessions/one/queue/q');
 expect(calls[0].method).toBe('DELETE');
 expect(calls[0].headers['X-Tau-CSRF']).toBe('1');
 await expect(client.removeQueueItem('', 'q')).rejects.toThrow('identity');
});
test('queue reorder uses explicit session and validates direction',async()=>{
 const calls=[];const client=createTauClient({fetchImpl:async(path,options)=>{calls.push({path,...options});return Response.json({queue_id:'q'});}});
 await client.moveQueueItem('one','q','up');
 expect(calls[0].path).toBe('/api/sessions/one/queue/q/move');
 expect(JSON.parse(calls[0].body)).toEqual({direction:'up'});
 expect(calls[0].headers['X-Tau-CSRF']).toBe('1');
 await expect(client.moveQueueItem('one','q','sideways')).rejects.toThrow('Invalid queue move');
});
test('status preserves explicit native activity metadata',async()=>{
 const client=createTauClient({fetchImpl:async()=>Response.json({runs:[{run_id:'r1',session_id:'one',status:'running',last_status:{type:'tool_use',title:'Running fixture tool',status:'Working'}}]})});
 expect((await client.status('one')).active_turns).toEqual([{turn_id:'r1',session_id:'one',started_at:undefined,last_status:{type:'tool_call',title:'Running fixture tool',status:'Working'}}]);
});
test('steering existing queue requires explicit active run',async()=>{
 const calls=[];const client=createTauClient({fetchImpl:async(path,options)=>{calls.push({path,...options});return Response.json({});}});
 await expect(client.steerQueueItem('one','q',null)).rejects.toThrow('active run');
 expect(calls).toHaveLength(0);
 await client.steerQueueItem('one','q','run-1');
 expect(calls[0].path).toBe('/api/sessions/one/queue/q/steer');
 expect(JSON.parse(calls[0].body)).toEqual({run_id:'run-1'});
 expect(calls[0].headers['X-Tau-CSRF']).toBe('1');
});
test('commands use the authoritative session-scoped native catalogue',async()=>{
 const paths=[];const client=createTauClient({fetchImpl:async path=>{paths.push(path);return Response.json({commands:[{name:'/skill:demo',description:'Demo'}]});}});
 expect(await client.commands('session a')).toEqual({commands:[{name:'/skill:demo',description:'Demo'}]});
 expect(paths).toEqual(['/api/commands?session_id=session%20a']);
});
test('manual compaction uses the dedicated scoped endpoint',async()=>{
 const calls=[];const client=createTauClient({fetchImpl:async(path,options)=>{calls.push({path,...options});return Response.json({session_id:'one',summary:'done'});}});
 expect(await client.compact('one',' keep decisions ')).toEqual({session_id:'one',summary:'done'});
 expect(calls[0].path).toBe('/api/sessions/one/compact');
 expect(JSON.parse(calls[0].body)).toEqual({instructions:'keep decisions'});
 expect(calls[0].headers['X-Tau-CSRF']).toBe('1');
});
test('context maps only explicitly labelled valid local estimates',async()=>{
 let payload={estimated_tokens:16384,context_window:65536,token_usage_source:'local_estimate',compact_command:'/compact'};
 const client=createTauClient({fetchImpl:async()=>Response.json(payload)});
 const context=await client.context('one');expect(context.percent).toBe(25);expect(context.source).toBe('local_estimate');expect(context.compactCommand).toBe('/compact');
 payload={estimated_tokens:0,context_window:65536,token_usage_source:'local_estimate'};
 expect((await client.context('one')).percent).toBe(0);
 payload={estimated_tokens:-1,context_window:65536,token_usage_source:'local_estimate'};
 expect((await client.context('one')).percent).toBeUndefined();
 payload={estimated_tokens:12,context_window:65536,token_usage_source:'unknown'};
 expect((await client.context('one')).percent).toBeUndefined();
});

test('session picker handle formatter matches canonical display rules', async () => {
 const {sessionHandle}=await import('../static/js/components/session-picker.js');
 expect(sessionHandle('Fixture session')).toBe('@fixture-session');
 expect(sessionHandle('  Research  ')).toBe('@research');
 expect(sessionHandle('A / B')).toBe('@a-b');
});

test('model catalogue preserves explicit capability metadata', async () => {
 const client=createTauClient({fetchImpl:async path=>Response.json(path==='/api/models'
  ? {source:'configured',models:[{provider_name:'provider',model:'model',supports_thinking:true,context_window:65536,thinking_levels:['off','low','medium','high']}]}
  : {...session,provider_name:'provider',model:'model',updated_at:'r1'})});
 const result=await client.models('one');
 expect(result.models).toEqual([{id:'model',provider:'provider',name:'model',reasoning:true,contextWindow:65536,thinkingLevels:['off','low','medium','high']}]);
 expect(result.thinking_levels).toEqual(['off','low','medium','high']);
});
