/** External module entrypoint; errors render as text, never executable HTML. */
function showFailure(message) {
    const root=document.getElementById('app');
    if(!root)return;
    const error=document.createElement('pre');
    error.setAttribute('role','alert');
    error.textContent=`Unable to start Tau: ${message}`;
    root.replaceChildren(error);
}
async function start() {
    await import('/static/extension-ui.js');
    await import('/static/frontend-sdk.js');
    await import('/static/dist/app.js?v=1');
}
start().catch(error=>showFailure(error.message||String(error)));
