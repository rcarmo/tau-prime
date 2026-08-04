const CACHE_NAME = "tau-web-shell-v1";
const SHELL_URLS = Object.freeze([
  "/",
  "/index.html",
  "/manifest.webmanifest",
  "/static/app.css",
  "/static/app.js",
]);

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      await cache.addAll(SHELL_URLS);
      await self.skipWaiting();
    })(),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames
          .filter((cacheName) => cacheName !== CACHE_NAME)
          .map((cacheName) => caches.delete(cacheName)),
      );
      await self.clients.claim();
    })(),
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }

  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) {
    return;
  }
  if (!SHELL_URLS.includes(url.pathname)) {
    return;
  }

  event.respondWith(
    (async () => {
      const cached = await caches.match(event.request, { ignoreSearch: true });
      if (cached) {
        return cached;
      }

      const response = await fetch(event.request);
      const cache = await caches.open(CACHE_NAME);
      await cache.put(event.request, response.clone());
      return response;
    })(),
  );
});
