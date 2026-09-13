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
