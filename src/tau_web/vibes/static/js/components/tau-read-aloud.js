import {html,useEffect,useState} from '../vendor/preact-htm.js';
import {speechText} from '../tau-speech-text.js';
let owner=null;
export function TauReadAloud({text}){
 const [active,setActive]=useState(false);
 useEffect(()=>()=>{if(owner?.stop===setActive){window.speechSynthesis?.cancel();owner=null;}},[]);
 if(!window.speechSynthesis||typeof window.SpeechSynthesisUtterance!=='function'||!text?.trim())return null;
 const toggle=e=>{
  e.stopPropagation();
  if(owner){const previous=owner;owner=null;window.speechSynthesis.cancel();previous.stop(false);if(previous.stop===setActive)return;}
  const utterance=new window.SpeechSynthesisUtterance(speechText(text));
  const current={stop:setActive};owner=current;
  const finish=()=>{if(owner===current){owner=null;setActive(false);}};
  utterance.onend=finish;utterance.onerror=finish;
  setActive(true);window.speechSynthesis.speak(utterance);
 };
 return html`<button class=${`post-action-btn post-speak-btn${active?' is-active':''}`} type="button" title=${active?'Stop reading aloud':'Read aloud'} aria-label=${active?'Stop reading aloud':'Read aloud'} onClick=${toggle}><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">${active?html`<rect x="6" y="6" width="12" height="12" rx="2"/>`:html`<path d="M11 5 6 9H3v6h3l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/><path d="M18 6a8.5 8.5 0 0 1 0 12"/>`}</svg></button>`;
}
