/** Piclaw-compatible bounded text for browser speech synthesis. */
export function speechText(value){
 return String(value||'').replace(/```[\s\S]*?```/g,' Code block omitted. ')
 .replace(/`([^`]+)`/g,'$1').replace(/!\[([^\]]*)\]\(([^)]+)\)/g,'$1')
 .replace(/\[([^\]]+)\]\(([^)]+)\)/g,'$1').replace(/^#{1,6}\s+/gm,'')
 .replace(/^>\s?/gm,'').replace(/^[-*+]\s+/gm,'• ').replace(/\n{3,}/g,'\n\n')
 .replace(/\n\n+/g,'. ').replace(/\s+/g,' ').replace(/\s+([.,;:!?])/g,'$1').trim().slice(0,1600);
}
