import type { ComponentChildren } from 'preact';
import { useLayoutEffect, useRef } from 'preact/hooks';

export function ClassicSettingsDialog({ open, onClose, children }: {open:boolean;onClose:()=>void;children:ComponentChildren}) {
  const backdrop=useRef<HTMLDivElement>(null);
  const close=useRef(onClose);close.current=onClose;
  useLayoutEffect(()=>{
    if(!open || !backdrop.current)return;
    const previous=document.activeElement as HTMLElement|null;
    const inert:Array<[HTMLElement,boolean]>=[];
    let node:HTMLElement=backdrop.current;
    while(node.parentElement && node!==document.body){
      for(const sibling of Array.from(node.parentElement.children))if(sibling!==node && sibling instanceof HTMLElement){inert.push([sibling,sibling.inert]);sibling.inert=true;}
      node=node.parentElement;
    }
    const controls=()=>Array.from(backdrop.current!.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]')).filter(el=>el.getClientRects().length>0);
    backdrop.current.querySelector<HTMLButtonElement>('.settings-dialog-close')?.focus();
    const key=(event:KeyboardEvent)=>{
      if(event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();close.current();}
      if(event.key==='Tab'){const list=controls(),first=list[0],last=list.at(-1);if(!first)return;
        if(event.shiftKey && (document.activeElement===first || !backdrop.current?.contains(document.activeElement))){event.preventDefault();last?.focus();}
        else if(!event.shiftKey && document.activeElement===last){event.preventDefault();first.focus();}
      }
    };
    document.addEventListener('keydown',key,true);
    return ()=>{document.removeEventListener('keydown',key,true);for(const [el,value]of inert)el.inert=value;if(previous?.isConnected && !previous.closest('[inert]'))previous.focus();};
  },[open]);
  return <div ref={backdrop} className="settings-dialog-overlay" hidden={!open} onClick={event=>{if(event.target===event.currentTarget)onClose();}}>
    <section className="settings-dialog" role="dialog" aria-modal="true" aria-labelledby="classic-settings-title">
      <header className="settings-dialog-header"><h2 id="classic-settings-title" className="settings-dialog-title">Settings</h2><button className="settings-dialog-close" type="button" aria-label="Close settings" onClick={onClose}>✕</button></header>
      {children}
    </section>
  </div>;
}
