/** Incremental SSE decoding for Tau's authenticated fetch stream. */
export async function consumeTauEvents(body, onFrame, signal) {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let frame = { event: 'message', data: [], id: null };
    function line(value) {
        if (!value) {
            if (frame.data.length) onFrame({ event: frame.event, id: frame.id, data: JSON.parse(frame.data.join('\n')) });
            frame = { event: 'message', data: [], id: null };
            return;
        }
        if (value.startsWith(':')) return;
        const colon = value.indexOf(':');
        const key = colon < 0 ? value : value.slice(0, colon);
        let text = colon < 0 ? '' : value.slice(colon + 1);
        if (text.startsWith(' ')) text = text.slice(1);
        if (key === 'data') frame.data.push(text);
        if (key === 'event') frame.event = text;
        if (key === 'id' && !text.includes('\0')) frame.id = text;
    }
    const abort = () => { void reader.cancel().catch(() => {}); };
    signal?.addEventListener('abort', abort, { once: true });
    try {
        while (!signal?.aborted) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            let end;
            while ((end = buffer.indexOf('\n')) >= 0) {
                line(buffer.slice(0, end).replace(/\r$/, ''));
                buffer = buffer.slice(end + 1);
            }
            if (buffer.length > 4 * 1024 * 1024 || frame.data.join('').length > 4 * 1024 * 1024) throw new Error('Tau SSE frame exceeds limit');
        }
    } finally {
        signal?.removeEventListener('abort', abort);
        await reader.cancel().catch(() => {});
        reader.releaseLock();
    }
}

export class TauEventStream {
    constructor({ onFrame, onStatus = () => {}, getToken = () => '', fetchImpl = fetch, retryMs = 1000 }) {
        Object.assign(this, { onFrame, onStatus, getToken, fetchImpl, retryMs });
        this.cursor = null;
        this.seenEvents = new Set();
        this.controller = null;
        this.timer = null;
        this.connected = false;
        this.connecting = false;
    }
    reconnectIfNeeded() {
        if (!this.connected && !this.connecting) this.connect();
    }
    connect() {
        this.disconnect();
        const controller = new AbortController();
        this.controller = controller;
        const run = async () => {
            if (controller.signal.aborted) return;
            this.connecting = true;
            this.onStatus('connecting');
            try {
                const headers = { Accept: 'text/event-stream' };
                const token = this.getToken();
                if (token) headers.Authorization = `Bearer ${token}`;
                if (this.cursor !== null) headers['Last-Event-ID'] = this.cursor;
                const response = await this.fetchImpl('/api/events', { headers, credentials: 'same-origin', signal: controller.signal });
                if (!response.ok || !response.body || !response.headers.get('Content-Type')?.includes('text/event-stream')) throw new Error(`Tau event stream unavailable (${response.status})`);
                if (controller.signal.aborted) return;
                this.connecting = false;
                this.connected = true;
                this.onStatus('connected');
                await consumeTauEvents(response.body, frame => {
                    if (controller.signal.aborted) return;
                    const eventId = frame.data?.event_id;
                    if (!eventId || !this.seenEvents.has(eventId)) {
                        this.onFrame(frame);
                        if (eventId) {
                            this.seenEvents.add(eventId);
                            if (this.seenEvents.size > 4096) this.seenEvents.delete(this.seenEvents.values().next().value);
                        }
                    }
                    if (frame.id !== null) this.cursor = frame.id;
                }, controller.signal);
            } catch (error) {
                if (!controller.signal.aborted) this.lastError = error;
            }
            if (!controller.signal.aborted) {
                this.connecting = false;
                this.connected = false;
                this.onStatus('disconnected');
                this.timer = setTimeout(run, this.retryMs);
            }
        };
        void run();
    }
    disconnect() {
        this.connecting = false;
        this.connected = false;
        this.controller?.abort();
        clearTimeout(this.timer);
        this.timer = null;
    }
}
