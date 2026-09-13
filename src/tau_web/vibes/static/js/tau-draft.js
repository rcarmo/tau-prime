/** Session/run-scoped transient text; persisted timeline remains authoritative. */
export function reduceTauDraft(state, frame, sessionId) {
    if (frame.event === 'tau.snapshot') return {runId:null,text:''};
    const data=frame.data||{}, payload=data.payload||{};
    if (!sessionId || data.session_id!==sessionId || !data.run_id) return state;
    if (frame.event==='tau.agent.message_start' && payload.role==='assistant') return {runId:data.run_id,text:''};
    if (frame.event==='tau.agent.message_delta' && typeof payload.delta==='string') {
        if (state.runId && state.runId!==data.run_id) return state;
        return {runId:data.run_id,text:state.text+payload.delta};
    }
    if (frame.event==='tau.agent.message_end' && data.run_id===state.runId) return {runId:null,text:''};
    return state;
}
