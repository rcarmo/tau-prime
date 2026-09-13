import {html,useEffect,useState} from '../vendor/preact-htm.js';
import {getAgentStatus,cancelTauRun} from '../api.js';

/** Tau-specific cancellation; never infer acknowledgement from a local click. */
export function TauRunControl({sessionId}) {
    const [run,setRun]=useState(null);
    const [pending,setPending]=useState(false);
    const [error,setError]=useState('');
    useEffect(()=>{
        let disposed=false;
        let loading=false;
        setRun(null);setError('');setPending(false);
        if(!sessionId)return;
        const refresh=async()=>{
            if(loading)return;
            loading=true;
            try{
                const result=await getAgentStatus(sessionId);
                if(!disposed){setRun(result.active_turns.at(-1)||null);setError('');}
            }catch(e){if(!disposed)setError(e.message);}
            finally{loading=false;}
        };
        refresh();const timer=setInterval(refresh,2000);
        return()=>{disposed=true;clearInterval(timer);};
    },[sessionId]);
    const cancel=async()=>{
        if(!run||pending)return;
        setPending(true);setError('');
        try{
            const result=await cancelTauRun(run.turn_id);
            if(!result.accepted && ['pending','running'].includes(result.run?.status)) throw new Error('Tau did not accept cancellation');
            const status=await getAgentStatus(sessionId);
            setRun(status.active_turns.at(-1)||null);
        }catch(e){setError(e.message);}
        finally{setPending(false);}
    };
    return html`<div class="tau-run-control" aria-live="polite">
        ${run && html`<button type="button" class="compose-queue-btn" disabled=${pending} onClick=${cancel}>${pending?'Cancelling…':'Cancel run'}</button>`}
        ${error && html`<span role="alert">${error}</span>`}
    </div>`;
}
