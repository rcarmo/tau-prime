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
    expect(result.models).toEqual([{id:'model',provider:'provider',name:'model'}]);
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
