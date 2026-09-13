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
    return {
        async sessions(includeArchived = false) {
            const result = await request(`/sessions?include_archived=${includeArchived}`);
            return { sessions: result.sessions.map(sessionFromTau) };
        },
        async renameSession(id, name) {
            const result = await request(`/sessions/${encodeURIComponent(id)}`, { method: 'PATCH', body: { title: name } });
            return { session: sessionFromTau(result) };
        },
        async createSession({ name, provider, model }) {
            if (!provider || !model) throw new Error('Choose a provider and model before creating a Tau session');
            const result = await request('/sessions', { method: 'POST', body: { title: name, provider_name: provider, model } });
            return { session: sessionFromTau(result) };
        },
    };
}
