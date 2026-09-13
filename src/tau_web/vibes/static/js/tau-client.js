/** Tau transport boundary. Components must not interpret Tau REST resources. */
export function sessionFromTau(session) {
    if (!session.session_id) throw new Error('Tau session is missing its identity');
    return {
        id: session.session_id,
        name: session.title || session.session_id,
        model: session.model,
        provider: session.provider_name,
        created_at: session.created_at,
        updated_at: session.updated_at,
        archived: Boolean(session.archived_at),
    };
}

export function postFromTau(record) {
    let message = {};
    try { message = typeof record.content_blocks_json === 'string' ? JSON.parse(record.content_blocks_json) : record.content_blocks_json || {}; } catch { /* Keep text readable if legacy metadata is malformed. */ }
    return {
        id: record.message_id, timestamp: record.created_at,
        data: { type: record.role === 'assistant' ? 'agent_response' : record.role,
            content: record.content, session_id: record.session_id,
            tau_attachments: Array.isArray(message?.attachments) ? message.attachments.filter(item => typeof item?.media_id === 'string' && item.media_id) : [],
            tau_tool_calls: Array.isArray(message?.tool_calls) ? message.tool_calls : [],
            tau_tool_result: record.role === 'tool' ? { name: message?.name, callId: message?.tool_call_id, ok: message?.ok } : null },
    };
}

export function createTauClient({ fetchImpl = globalThis.fetch, getToken = () => '' } = {}) {
    async function request(path, { method = 'GET', body } = {}) {
        const headers = { Accept: 'application/json' };
        if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) headers['X-Tau-CSRF'] = '1';
        const token = getToken();
        if (token) headers.Authorization = `Bearer ${token}`;
        if (body !== undefined) headers['Content-Type'] = 'application/json';
        const response = await fetchImpl(`/api${path}`, {
            method, headers, credentials: 'same-origin',
            ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
        });
        if (!response.ok) {
            const payload = await response.json().catch(() => ({}));
            const error = new Error(typeof payload.error === 'string' ? payload.error : `Tau request failed (${response.status})`);
            error.status = response.status;
            error.code = payload.code;
            error.currentPlan = payload.plan;
            throw error;
        }
        return response.status === 204 ? null : response.json();
    }
    const revisions = new Map();
    async function loadSession(id) {
        const session = await request(`/sessions/${encodeURIComponent(id)}`);
        revisions.set(id, session.updated_at);
        return session;
    }
    return {
        async widgetDocument(extensionId, widgetId) {
            if (![extensionId, widgetId].every(id => typeof id === 'string' && /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(id))) throw new Error('Invalid widget identity');
            const token = getToken();
            const response = await fetchImpl(`/api/extensions/widgets/${encodeURIComponent(extensionId)}/${encodeURIComponent(widgetId)}`, { headers: token ? { Authorization: `Bearer ${token}` } : {}, credentials: 'same-origin' });
            if (!response.ok) throw new Error(`Widget refresh failed (${response.status})`);
            const text = await response.text();
            if (new TextEncoder().encode(text).byteLength > 2 * 1024 * 1024) throw new Error('Widget document exceeds limit');
            return text;
        },
        async frontendModules() {
            return (await request('/extensions/frontend-modules')).modules;
        },
        async extensionRequest(path, options = {}) {
            if (typeof path !== 'string' || !path.startsWith('/api/') || path.includes('\\') || path.includes('#')) throw new Error('Invalid extension API path');
            const url = new URL(path, 'http://tau.invalid');
            if (url.origin !== 'http://tau.invalid' || !url.pathname.startsWith('/api/')) throw new Error('Invalid extension API path');
            return request(url.pathname.slice(4) + url.search, options);
        },
        async dashboard(page = 1) {
            const token = getToken();
            const response = await fetchImpl(`/dashboard?page=${page}&page_size=8`, { headers: token ? { Authorization: `Bearer ${token}` } : {}, credentials: 'same-origin' });
            if (!response.ok) throw new Error(`Tau dashboard unavailable (${response.status})`);
            return response.json();
        },
        async meters() {
            const token = getToken();
            const response = await fetchImpl('/meters', { headers: token ? { Authorization: `Bearer ${token}` } : {}, credentials: 'same-origin' });
            if (!response.ok) throw new Error(`Tau metrics unavailable (${response.status})`);
            return response.json();
        },
        async branches(id) {
            if (!id) return [];
            return (await request(`/sessions/${encodeURIComponent(id)}/branches`)).branches;
        },
        async selectBranch(id, leaf) {
            if (!id || typeof leaf !== 'string' || !leaf) throw new Error('Select a valid conversation leaf');
            return request(`/sessions/${encodeURIComponent(id)}/branches/select`, { method: 'POST', body: { leaf_entry_id: leaf } });
        },
        async agentIdentity() {
            const settings = await request('/settings');
            return { agents: [{ id: 'default', name: settings.agent_name || 'Tau' }] };
        },
        async media(id) {
            if (!id) return [];
            return (await request(`/media?session_id=${encodeURIComponent(id)}`)).media;
        },
        async mediaBlob(id) {
            const headers = {}; const token = getToken();
            if (token) headers.Authorization = `Bearer ${token}`;
            const response = await fetchImpl(`/api/media/${encodeURIComponent(id)}/content`, { headers, credentials: 'same-origin' });
            if (!response.ok) throw new Error(`Tau download failed (${response.status})`);
            const limit = 32 * 1024 * 1024;
            if (Number(response.headers.get('Content-Length')) > limit) {
                await response.body?.cancel();
                throw new Error('Media exceeds the 32 MiB browser download limit');
            }
            if (!response.body) throw new Error('Tau media response has no body');
            const reader = response.body.getReader(); const chunks = []; let size = 0;
            try {
                while (true) {
                    const { value, done } = await reader.read(); if (done) break;
                    size += value.byteLength;
                    if (size > limit) throw new Error('Media exceeds the 32 MiB browser download limit');
                    chunks.push(value);
                }
                return new Blob(chunks, { type: response.headers.get('Content-Type') || 'application/octet-stream' });
            } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
        },
        async upload(file, { sessionId, signal } = {}) {
            if (!sessionId || sessionId === 'default') throw new Error('Select a session before uploading');
            const body = new FormData(); body.append('file', file, file.name); body.append('session_id', sessionId);
            const headers = { 'X-Tau-CSRF': '1' }; const token = getToken();
            if (token) headers.Authorization = `Bearer ${token}`;
            const response = await fetchImpl('/api/media', { method: 'POST', headers, body, signal, credentials: 'same-origin' });
            if (!response.ok) throw new Error(`Tau upload failed (${response.status})`);
            const media = await response.json();
            return { ...media, id: media.media_id };
        },
        async approvals(id) {
            if (!id) return [];
            const result = await request(`/sessions/${encodeURIComponent(id)}/approvals`);
            return result.approvals;
        },
        async resolveApproval(id, decision) {
            if (!id || !['allow', 'deny'].includes(decision)) throw new Error('Invalid approval decision');
            return request(`/approvals/${encodeURIComponent(id)}`, { method: 'POST', body: { decision } });
        },
        async plan(id) {
            if (!id) throw new Error('Select a session to load its plan');
            return request(`/sessions/${encodeURIComponent(id)}/plan`);
        },
        async savePlan(id, markdown, revision) {
            if (!id) throw new Error('Select a session to save its plan');
            if (revision !== null && (!Number.isInteger(revision) || revision < 0)) throw new Error('Invalid plan revision');
            return request(`/sessions/${encodeURIComponent(id)}/plan`, {
                method: 'PUT', body: { markdown, expected_revision: revision },
            });
        },
        async search(query, limit = 50, offset = 0, filters = {}) {
            if (offset || filters.images || filters.attachments || filters.threadId || filters.scope === 'root') throw new Error('This search filter is not supported by Tau');
            const params = new URLSearchParams({ q: query, limit: String(limit) });
            if (filters.sessionId) params.set('session_id', filters.sessionId);
            const result = await request(`/search?${params}`);
            return { results: result.results.map(item => ({
                id: `search:${item.entity_type}:${item.entity_id}`, timestamp: null,
                data: { type: 'search_result', content: item.text, session_id: item.session_id,
                    entity_type: item.entity_type, entity_id: item.entity_id },
            })) };
        },
        async workspaceFile(path, maxBytes = 20000) {
            const result = await request(`/files?path=${encodeURIComponent(path)}`);
            if (result.kind !== 'file' || typeof result.content !== 'string') throw new Error('Tau text preview is unavailable for this file');
            const bytes = new TextEncoder().encode(result.content);
            const limit = Math.max(0, Math.min(1000000, Number(maxBytes) || 20000));
            return { path: result.path, kind: 'text', text: new TextDecoder().decode(bytes.slice(0, limit), { stream: bytes.length > limit }),
                size: result.size_bytes, content_type: 'text/plain', truncated: bytes.length > limit, read_only: true };
        },
        async workspaceTree(path = '', depth = 2, showHidden = false) {
            const read = async (current, remaining) => {
                const result = await request(`/files?path=${encodeURIComponent(current)}`);
                if (result.kind !== 'directory') throw new Error('Expected a Tau directory');
                const children = [];
                for (const entry of result.entries) {
                    if (!showHidden && entry.name.startsWith('.')) continue;
                    if (!['directory', 'file'].includes(entry.kind)) continue;
                    if (entry.kind === 'directory' && remaining > 1) children.push(await read(entry.path, remaining - 1));
                    else children.push({ name: entry.name, path: entry.path, type: entry.kind === 'directory' ? 'dir' : 'file' });
                }
                return { name: current.split('/').pop() || 'Workspace', path: current || '.', type: 'dir', children };
            };
            return { root: await read(path, Math.max(1, Math.min(3, depth))) };
        },
        async onboarding() { return request('/onboarding'); },
        async configureProvider({ provider, model, credential }) {
            if (!provider?.trim() || !model?.trim()) throw new Error('Provider and model are required');
            return request('/onboarding', { method: 'PUT', body: { provider: provider.trim(), model: model.trim(), ...(credential ? { credential } : {}) } });
        },
        async context(id) {
            if (!id) return null;
            const result = await request(`/sessions/${encodeURIComponent(id)}/context`);
            return { entryCount: result.entry_count, messageCount: result.message_count,
                compactionCount: result.compaction_count, activeLeafEntryId: result.active_leaf_entry_id };
        },
        async cancelRun(runId) {
            if (!runId) throw new Error('A Tau run ID is required');
            return request(`/runs/${encodeURIComponent(runId)}/cancel`, { method: 'POST' });
        },
        async status(id) {
            if (!id) return { active_turns: [] };
            const result = await request(`/sessions/${encodeURIComponent(id)}/runs`);
            return { active_turns: result.runs.filter(run => ['pending', 'running'].includes(run.status)).map(run => ({
                turn_id: run.run_id, session_id: run.session_id,
                type: run.status === 'pending' ? 'queued' : 'thinking',
                started_at: run.started_at || run.created_at,
            })) };
        },
        async queue(id) {
            if (!id) return { items: [] };
            const result = await request(`/sessions/${encodeURIComponent(id)}/queue`);
            return { items: result.queue.map(item => ({
                row_id: item.queue_id, session_id: item.session_id,
                mode: item.queue_kind === 'steer' ? 'steer' : 'queued',
                content: typeof item.content === 'string' ? item.content : JSON.stringify(item.content),
                position: item.position, tau_readonly: true,
            })) };
        },
        async send(id, content, { mode = 'auto', mediaIds = [], intent = null } = {}) {
            if (!id || id === 'default') throw new Error('Select a Tau session before sending');
            if (!content?.trim()) throw new Error('Message is empty');
            if (mediaIds.some(id => typeof id !== 'string' || !id || /[\r\n\[\]]/.test(id))) throw new Error('Invalid Tau attachment reference');
            if (mediaIds.length) content += '\n\nAttachments (uploaded separately; references only, not inline media):\n' + mediaIds.map(id => `- [media:${id}]`).join('\n');
            if (intent || content.trimStart().startsWith('/')) throw new Error('Tau command submission is not integrated yet');
            if (!['auto', 'run', 'steer', 'follow_up', 'queue'].includes(mode)) throw new Error('Unsupported Tau delivery mode');
            if (mode === 'auto') {
                const result = await request(`/sessions/${encodeURIComponent(id)}/runs`);
                mode = result.runs.some(run => ['pending', 'running'].includes(run.status)) ? 'follow_up' : 'run';
            }
            if (mode === 'run') {
                const run = await request(`/sessions/${encodeURIComponent(id)}/runs`, { method: 'POST', body: { content } });
                return { accepted: true, run_id: run.run_id };
            }
            const item = await request(`/sessions/${encodeURIComponent(id)}/queue`, {
                method: 'POST', body: { content, kind: mode === 'steer' ? 'steer' : 'follow_up' },
            });
            return { accepted: true, queued: true, queue_id: item.queue_id };
        },
        async timeline(id, limit = 10, before = null) {
            if (!id || id === 'default') throw new Error('Select a real Tau session before loading messages');
            if (!Number.isInteger(limit) || limit < 1) throw new Error('Invalid timeline page size');
            const records = [];
            let after = 0;
            // Tau exposes ascending pagination only. Scan it explicitly until a
            // reverse-page backend endpoint exists; never claim a partial scan complete.
            for (let page = 0; ; page++) {
                if (page >= 1000) throw new Error('Timeline scan limit exceeded');
                const result = await request(`/sessions/${encodeURIComponent(id)}/timeline?after=${after}&limit=200`);
                const batch = result.timeline;
                for (const record of batch) {
                    if (!Number.isInteger(record.message_id) || record.message_id <= after) throw new Error('Invalid Tau timeline cursor');
                    after = record.message_id;
                    if (before === null || record.message_id < Number(before)) records.push(record);
                }
                if (batch.length < 200 || (before !== null && after >= Number(before))) break;
            }
            return { posts: records.slice(-limit).reverse().map(postFromTau), has_more: records.length > limit };
        },
        async modelState(id) {
            const session = await loadSession(id);
            return { available: true, model: { provider: session.provider_name, id: session.model, name: session.model }, thinking_level: session.thinking_level };
        },
        async models(id) {
            const [catalogue, session] = await Promise.all([request('/models'), loadSession(id)]);
            const models = new Map();
            for (const item of [...catalogue.models, session]) {
                const model = item.model;
                const provider = item.provider_name;
                models.set(JSON.stringify([provider, model]), { id: model, provider, name: model });
            }
            return {
                available: true, source: catalogue.source,
                models: [...models.values()],
                current_model: { provider: session.provider_name, id: session.model },
                // Configurable Tau policy values, not discovered model capabilities.
                thinking_levels: ['off', 'minimal', 'low', 'medium', 'high', 'xhigh'],
            };
        },
        async changeModel(id, changes) {
            const { provider, model_id: model } = changes;
            if (Object.hasOwn(changes, 'thinking_level')) {
                const level = changes.thinking_level;
                if (level !== null && !['off', 'minimal', 'low', 'medium', 'high', 'xhigh'].includes(level)) throw new Error('Invalid Tau thinking level');
                if (!revisions.has(id)) throw new Error('Load model state before changing it');
                const session = await request(`/sessions/${encodeURIComponent(id)}/thinking`, {
                    method: 'PATCH', body: { thinking_level: level, expected_updated_at: revisions.get(id) },
                });
                revisions.set(id, session.updated_at);
                return { available: true, model: { provider: session.provider_name, id: session.model, name: session.model }, thinking_level: session.thinking_level };
            }
            if (!provider || !model) throw new Error('A provider and model are required');
            if (!revisions.has(id)) throw new Error('Load model state before changing it');
            const session = await request(`/sessions/${encodeURIComponent(id)}/model`, {
                method: 'PATCH', body: { provider_name: provider, model, expected_updated_at: revisions.get(id) },
            });
            revisions.set(id, session.updated_at);
            return { available: true, model: { provider: session.provider_name, id: session.model, name: session.model }, thinking_level: session.thinking_level };
        },
        async sessions(includeArchived = false) {
            const result = await request(`/sessions?include_archived=${includeArchived}`);
            return { sessions: result.sessions.map(sessionFromTau) };
        },
        async archiveSession(id, archived) {
            const result = await request(`/sessions/${encodeURIComponent(id)}${archived ? '' : '/restore'}`, { method: archived ? 'DELETE' : 'POST' });
            return { session: sessionFromTau(result) };
        },
        async renameSession(id, name) {
            const result = await request(`/sessions/${encodeURIComponent(id)}`, { method: 'PATCH', body: { title: name } });
            return { session: sessionFromTau(result) };
        },
        async createSession({ name, provider, model, useConfiguredDefaults = false }) {
            if (useConfiguredDefaults && !provider && !model) {
                const setup = await request('/onboarding');
                provider = setup.default_provider;
                model = setup.default_model;
            }
            if (!provider || !model) throw new Error('Choose a provider and model in Tau provider setup before creating a session');
            const result = await request('/sessions', { method: 'POST', body: { title: name, provider_name: provider, model } });
            return { session: sessionFromTau(result) };
        },
    };
}
