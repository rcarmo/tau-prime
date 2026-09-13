/** Never replace an explicitly requested session with an unrelated one. */
export function initialTauSession(sessions, search = '') {
    const requested = new URLSearchParams(search).get('session');
    if (requested) {
        if (!sessions.some(session => session.id === requested && !session.archived)) {
            throw new Error(`Requested Tau session is unavailable: ${requested}`);
        }
        return requested;
    }
    return sessions.find(session => !session.archived)?.id ?? null;
}
