import {test, expect} from 'bun:test';

test('imported UI session/model functions use Tau transport and token', async()=> {
    const originalFetch=globalThis.fetch;
    const originalStorage=Object.getOwnPropertyDescriptor(globalThis,'localStorage');
    const calls=[];
    try {
        Object.defineProperty(globalThis,'localStorage',{configurable:true,value:{getItem:()=> 'fixture-token'}});
        globalThis.fetch=async(path,options)=> {
            calls.push({path,options});
            const session={session_id:'actual',title:'Real session',provider_name:'p',model:'m',updated_at:'r1'};
            return Response.json(path.startsWith('/api/sessions?') ? {sessions:[session]} : session);
        };
        const api=await import('../static/js/api.js');
        expect((await api.getSessions()).sessions[0].id).toBe('actual');
        expect((await api.getSessionModelState('actual')).model).toEqual({provider:'p',id:'m',name:'m'});
        await api.changeSessionModel('actual',{provider:'p',model_id:'new'});
        expect(calls.map(call=>call.path)).toEqual(['/api/sessions?include_archived=false','/api/sessions/actual','/api/sessions/actual/model']);
        expect(calls[0].options.headers.Authorization).toBe('Bearer fixture-token');
        expect(JSON.parse(calls[2].options.body).expected_updated_at).toBe('r1');
        await expect(api.deleteSession('actual')).rejects.toThrow('archival');
        expect(calls.length).toBe(3);
    } finally {
        globalThis.fetch=originalFetch;
        if(originalStorage) Object.defineProperty(globalThis,'localStorage',originalStorage);
        else delete globalThis.localStorage;
    }
});
