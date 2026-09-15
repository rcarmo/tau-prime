import {html,useLayoutEffect,useRef,useState} from '../vendor/preact-htm.js';

function accentRgb(){
 const value=getComputedStyle(document.documentElement).getPropertyValue('--accent-color').trim()||'#1d9bf0';
 const hex=value.match(/^#([0-9a-f]{6})$/i)?.[1];
 return hex?`${parseInt(hex.slice(0,2),16)}, ${parseInt(hex.slice(2,4),16)}, ${parseInt(hex.slice(4),16)}`:'29, 155, 240';
}

/** Lazily loaded editor; the owner remains the sole source of Plan draft state. */
export function TauPlanEditor({value,onChange,disabled}) {
 const host=useRef(null),view=useRef(null),latest=useRef({value,onChange,disabled}),applying=useRef(false);
 const [fallback,setFallback]=useState(false);
 latest.current={value,onChange,disabled};
 useLayoutEffect(()=>{
  let disposed=false,observer,media,updateTheme;
  import('../vendor/plan-codemirror.js').then(cm=>{
   if(disposed)return;
   const theme=new cm.Compartment(),editable=new cm.Compartment();
   media=window.matchMedia('(prefers-color-scheme: dark)');
   const themes=()=>{const rgb=accentRgb(),accent=getComputedStyle(document.documentElement).getPropertyValue('--accent-color').trim()||'#1d9bf0';return [(document.documentElement.dataset.theme==='dark'||(!document.documentElement.dataset.theme&&media.matches))?cm.githubDark:cm.githubLight,cm.EditorView.theme({
    '&':{height:'100%',fontSize:'13px',background:'var(--bg-primary,#0b1020)',color:'var(--text-primary,#e5e7eb)'},
    '.cm-scroller':{overflow:'auto',fontFamily:'var(--font-mono, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace)',lineHeight:'1.45',background:'var(--bg-primary,#0b1020)'},
    '.cm-content':{padding:'12px',caretColor:accent},'.cm-gutters':{display:'none'},
    '.cm-line':{color:'var(--text-primary,#e5e7eb)',padding:'1px 8px',borderLeft:'3px solid transparent',borderRadius:'6px'},
    '.cm-lineWrapping .cm-line':{overflowWrap:'anywhere'},
    '.cm-cursor, .cm-dropCursor':{borderLeftColor:accent,borderLeftWidth:'2px'},
    '&.cm-focused .cm-cursor':{borderLeftColor:accent,borderLeftWidth:'2px'},
    '&.cm-focused .cm-selectionBackground, .cm-selectionBackground':{backgroundColor:`rgba(${rgb}, 0.22) !important`},
    '.cm-activeLine':{backgroundColor:`rgba(${rgb}, 0.07)`},'.cm-selectionMatch':{backgroundColor:`rgba(${rgb}, 0.16)`},'.cm-focused':{outline:'none'},
   })];};
   const decorations=editor=>{
    const ranges=[];
    for(let n=1;n<=editor.state.doc.lines;n++){
     const line=editor.state.doc.line(n),match=line.text.match(/^(\s*(?:[-*+]|\d+[.)])\s+)\[([ xX-])\](\s+)(.*)$/);
     if(!match)continue;
     const status=/x/i.test(match[2])?'completed':match[2]==='-'?'current':'pending';
     ranges.push(cm.Decoration.line({class:`plan-sidebar-cm-line plan-sidebar-cm-line-${status}`}).range(line.from));
     const start=line.from+match[1].length;
     ranges.push(cm.Decoration.mark({class:`plan-sidebar-cm-checkbox plan-sidebar-cm-checkbox-${status}`}).range(start,start+3));
     const content=start+3+match[3].length;
     if(content<line.to)ranges.push(cm.Decoration.mark({class:`plan-sidebar-cm-text plan-sidebar-cm-text-${status}`}).range(content,line.to));
    }
    return cm.Decoration.set(ranges,true);
   };
   const checklist=cm.ViewPlugin.fromClass(class {
    constructor(editor){this.decorations=decorations(editor);}
    update(update){if(update.docChanged||update.viewportChanged||update.selectionSet)this.decorations=decorations(update.view);}
   },{decorations:plugin=>plugin.decorations});
   const editor=new cm.EditorView({parent:host.current,state:cm.EditorState.create({doc:latest.current.value,extensions:[
    cm.minimalSetup,cm.markdown(),cm.EditorState.tabSize.of(2),cm.EditorView.lineWrapping,
    cm.EditorView.contentAttributes.of({'aria-label':'Plan markdown'}),
    theme.of(themes()),editable.of(cm.EditorState.readOnly.of(latest.current.disabled)),checklist,
    cm.EditorView.updateListener.of(update=>{if(update.docChanged&&!applying.current)latest.current.onChange(update.state.doc.toString());}),
   ]})});
   view.current={editor,cm,editable};
   updateTheme=()=>editor.dispatch({effects:theme.reconfigure(themes())});
   observer=new MutationObserver(updateTheme);
   media.addEventListener('change',updateTheme);
   if(!latest.current.disabled)editor.focus();
   observer.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme','class']});
  }).catch(error=>{console.warn('Plan editor initialization failed:',error);if(!disposed)setFallback(true);});
  return()=>{disposed=true;observer?.disconnect();if(updateTheme)media?.removeEventListener('change',updateTheme);view.current?.editor.destroy();view.current=null;};
 },[]);
 useLayoutEffect(()=>{
  const current=view.current;if(!current)return;
  applying.current=true;
  try{
   const spec={effects:current.editable.reconfigure(current.cm.EditorState.readOnly.of(disabled))};
   if(current.editor.state.doc.toString()!==value)spec.changes={from:0,to:current.editor.state.doc.length,insert:value};
   current.editor.dispatch(spec);
  }finally{applying.current=false;}
 },[value,disabled]);
 return html`<div class="plan-sidebar-editor" ref=${host}>${fallback&&html`<textarea aria-label="Plan markdown" value=${value} disabled=${disabled} onInput=${e=>onChange(e.target.value)} />`}</div>`;
}
