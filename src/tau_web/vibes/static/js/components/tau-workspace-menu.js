import {html,render,useEffect,useRef,useState} from '../vendor/preact-htm.js';

/** Body-mounted reference workspace menu; actions remain owned by Tau. */
export function TauWorkspaceMenu({workspaceOpen,onToggleWorkspace,onOpenTerminal}){
 const portal=useRef(null),button=useRef(null),[open,setOpen]=useState(false);
 useEffect(()=>{
  const root=document.createElement('div');root.className='timeline-menu-portal';document.body.appendChild(root);portal.current=root;
  return()=>{render(null,root);root.remove();portal.current=null;};
 },[]);
 useEffect(()=>{setOpen(false);},[workspaceOpen]);
 useEffect(()=>{
  const root=portal.current;if(!root)return;
  const place=()=>{root.style.left='8px';root.style.top='calc(env(safe-area-inset-top, 0px) + 8px)';};
  place();window.addEventListener('resize',place);const observer=new ResizeObserver(place);const sidebar=document.querySelector('.workspace-sidebar');if(sidebar)observer.observe(sidebar);
  const action=fn=>{setOpen(false);fn();requestAnimationFrame(()=>button.current?.focus());};
  render(html`<button ref=${button} type="button" class=${`timeline-menu-btn${open?' active':''}`} data-testid="hamburger" title="Workspace menu" aria-label="Workspace menu" aria-haspopup="menu" aria-expanded=${open} onClick=${()=>setOpen(v=>!v)}><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg></button>
  ${open&&html`<div class="timeline-menu-dropdown workspace-menu-dropdown" role="menu">
   <button role="menuitem" onClick=${()=>action(onToggleWorkspace)}>${workspaceOpen?'Hide workspace':'Show workspace'}</button>
   ${onOpenTerminal&&html`<button role="menuitem" onClick=${()=>action(onOpenTerminal)}>Open terminal</button>`}
   ${workspaceOpen&&html`<button role="menuitem" onClick=${()=>action(()=>document.querySelector('.workspace-refresh')?.click())}>Refresh</button><button role="menuitem" onClick=${()=>action(()=>(()=>{document.querySelector('.workspace-menu-button')?.click();requestAnimationFrame(()=>document.querySelector('.workspace-toggle-hidden')?.click());})())}>Toggle hidden files</button>`}
  </div>`}`,root);
  return()=>{window.removeEventListener('resize',place);observer.disconnect();};
 },[open,workspaceOpen,onToggleWorkspace,onOpenTerminal]);
 useEffect(()=>{
  if(!open)return;const outside=e=>{if(!portal.current?.contains(e.target))setOpen(false);};const key=e=>{if(e.key==='Escape'){e.preventDefault();setOpen(false);button.current?.focus();}};
  document.addEventListener('mousedown',outside);document.addEventListener('keydown',key);
  return()=>{document.removeEventListener('mousedown',outside);document.removeEventListener('keydown',key);};
 },[open]);
 return null;
}
