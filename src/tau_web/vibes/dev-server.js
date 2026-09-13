/** Local integration server; never installed as a second production UI. */
import { resolve, sep, extname } from 'node:path';
import { realpath } from 'node:fs/promises';

const root = await realpath(resolve(process.env.TAU_VIBES_STATIC_ROOT || resolve(import.meta.dir, 'static')));
const allowed = new Set(['.html', '.js', '.css', '.json', '.png', '.svg', '.ico', '.ttf', '.woff', '.woff2']);

export function createHandler({ backend = 'http://127.0.0.1:8080', fetchImpl = fetch } = {}) {
    const target = new URL(backend);
    if (!['http:', 'https:'].includes(target.protocol)) throw new Error('Expected an HTTP Tau backend');
    return async request => {
        const url = new URL(request.url);
        if (url.pathname.startsWith('/api/') || process.env.TAU_VIBES_PROXY_ALL === '1') {
            const upstream = new URL(url.pathname + url.search, target);
            const headers = new Headers(request.headers);
            headers.delete('host');
            const origin = headers.get('origin');
            if (origin) {
                if (origin !== url.origin) return Response.json({error:'Foreign development origin'}, {status:403});
                headers.set('origin', target.origin);
            }
            try {
                return await fetchImpl(upstream, {
                    method: request.method, headers, redirect: 'manual',
                    body: ['GET', 'HEAD'].includes(request.method) ? undefined : request.body,
                    signal: request.signal,
                });
            } catch {
                return Response.json({error:'Tau backend unavailable'}, {status:502});
            }
        }
        if (!['GET', 'HEAD'].includes(request.method)) return new Response('Method not allowed', {status:405});
        const relative = url.pathname === '/' ? 'index.html'
            : url.pathname.startsWith('/static/') ? url.pathname.slice(8) : null;
        if (relative === null) return new Response('Not found', {status:404});
        try {
            const path = await realpath(resolve(root, decodeURIComponent(relative)));
            if (!path.startsWith(root + sep) || !allowed.has(extname(path))) return new Response('Not found', {status:404});
            const file = Bun.file(path);
            return new Response(request.method === 'HEAD' ? null : file, {headers:{'Content-Type':file.type, 'Cache-Control':'no-store', ...(process.env.TAU_VIBES_TEST_CSP ? {'Content-Security-Policy': "default-src 'self'; base-uri 'none'; connect-src 'self'; font-src 'self' data:; form-action 'self'; frame-ancestors 'none'; img-src 'self' blob: data:; manifest-src 'self'; object-src 'none'; script-src 'self' blob:; style-src 'self'; worker-src 'self'"} : {})}});
        } catch {
            return new Response('Not found', {status:404});
        }
    };
}

if (import.meta.main) {
    const server = Bun.serve({hostname:'127.0.0.1', port:Number(process.env.TAU_VIBES_PORT || 8893),
        fetch:createHandler({backend:process.env.TAU_VIBES_BACKEND || 'http://127.0.0.1:8080'})});
    console.log(`Tau Vibes integration UI: ${server.url}`);
}
