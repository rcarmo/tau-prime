/** External module entrypoint; errors render as text, never executable HTML. */
function showFailure(message) {
    const root=document.getElementById('app');
    if(!root)return;
    const error=document.createElement('pre');
    error.setAttribute('role','alert');
    error.textContent=`Unable to start Tau: ${message}`;
    root.replaceChildren(error);
}
import('/static/dist/app.js?v=1').catch(error=>showFailure(error.message||String(error)));
