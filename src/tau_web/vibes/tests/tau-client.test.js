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
