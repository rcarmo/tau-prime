import {test, expect} from 'bun:test';
import {createHandler} from '../dev-server.js';
const handler=createHandler();
test('development shell serves imported entrypoint', async()=> {
    const result=await handler(new Request('http://localhost/'));
    expect(result.status).toBe(200);
    expect(await result.text()).toContain('/static/dist/app.js');
});
test('source and traversal paths are not exposed', async()=> {
    for(const path of ['/package.json','/static/%2e%2e%2fpackage.json','/static/../LICENSE']) {
        expect((await handler(new Request(`http://localhost${path}`))).status).toBe(404);
    }
});
test('API proxy preserves authentication, query, status and event stream', async()=> {
    let seen;
    const proxy=createHandler({backend:'http://127.0.0.1:8892',fetchImpl:async(url,options)=> {
        seen={url:String(url),options};
        return new Response('event: test\ndata: {}\n\n',{headers:{'Content-Type':'text/event-stream'},status:200});
    }});
    const response=await proxy(new Request('http://localhost/api/events?after=7',{headers:{Authorization:'Bearer fixture','Last-Event-ID':'7'}}));
    expect(seen.url).toBe('http://127.0.0.1:8892/api/events?after=7');
    expect(seen.options.headers.get('Authorization')).toBe('Bearer fixture');
    expect(seen.options.headers.get('Last-Event-ID')).toBe('7');
    expect(response.headers.get('Content-Type')).toBe('text/event-stream');
    expect(await response.text()).toContain('event: test');
});
