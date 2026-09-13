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
    return {
        id: record.message_id, timestamp: record.created_at,
        data: { type: record.role === 'assistant' ? 'agent_response' : record.role,
            content: record.content, session_id: record.session_id },
    };
}

export function createTauClient({ fetchImpl = globalThis.fetch, getToken = () => '' } = {}) {
    async function request(path, { method = 'GET', body } = {}) {
        const headers = { Accept: 'application/json' };
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
            if (mediaIds.length) throw new Error('Tau attachment submission is not integrated yet');
            if (intent || content.trimStart().startsWith('/')) throw new Error('Tau command submission is not integrated yet');
            if (!['auto', 'steer', 'follow_up', 'queue'].includes(mode)) throw new Error('Unsupported Tau delivery mode');
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
                // Tau does not advertise per-model reasoning capabilities.
                thinking_levels: [],
            };
        },
        async changeModel(id, { provider, model_id: model }) {
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
