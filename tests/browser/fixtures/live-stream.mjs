// Screenshot-only transport fixture. Real SSE/recovery is tested separately.
// Finite route.fulfill bodies close immediately and race screenshot timing.
export async function installLiveStream(page, adapter) {
  await page.addInitScript(({ adapter }) => {
    if (adapter === 'tau') {
      const originalFetch = window.fetch.bind(window);
      window.fetch = (input, init) => {
        const url = new URL(typeof input === 'string' ? input : input.url ?? String(input), location.href);
        if (url.pathname !== '/api/events') return originalFetch(input, init);
        const stream = new ReadableStream({
          start(controller) {
            controller.enqueue(new TextEncoder().encode(': visual fixture\n\n'));
            const signal = init?.signal ?? input?.signal;
            if (signal?.aborted) controller.close();
            else signal?.addEventListener('abort', () => controller.close(), { once: true });
          },
        });
        return Promise.resolve(new Response(stream, { headers: { 'Content-Type': 'text/event-stream' } }));
      };
    } else {
      const NativeEventSource = window.EventSource;
      window.EventSource = class extends EventTarget {
        static CONNECTING = 0; static OPEN = 1; static CLOSED = 2;
        CONNECTING = 0; OPEN = 1; CLOSED = 2;
        readyState = 0; onopen = null; onerror = null; onmessage = null;
        constructor(url, options) {
          super();
          if (new URL(url, location.href).pathname !== '/sse/stream') return new NativeEventSource(url, options);
          this.url = new URL(url, location.href).href;
          this.withCredentials = Boolean(options?.withCredentials);
          setTimeout(() => {
            if (this.readyState === 2) return;
            this.readyState = 1;
            const event = new Event('open');
            this.onopen?.(event); this.dispatchEvent(event);
          }, 0);
        }
        close() { this.readyState = 2; }
      };
    }
  }, { adapter });
}
