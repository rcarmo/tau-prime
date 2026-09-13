/* One-time upgrade worker: retire only Tau shell caches, never unrelated caches. */
self.addEventListener('install', event => event.waitUntil(self.skipWaiting()));
self.addEventListener('activate', event => event.waitUntil((async () => {
    for (const name of await caches.keys()) {
        if (name.startsWith('tau-web-shell-')) await caches.delete(name);
    }
    await self.clients.claim();
    await self.registration.unregister();
})()));
// No fetch interception: online requests go to the replacement server routes.
