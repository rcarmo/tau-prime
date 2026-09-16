import {test,expect} from 'bun:test';
import {parseQueuedContent} from '../static/js/components/queued-content.js';

test('queued payload reconstructs text and supported references without leaking metadata',()=>{
 const result=parseQueuedContent(`Inspect these inputs

Files:
- src/app.js
Folders:
- docs
Referenced messages:
- message:42
Attachments:
- attachment:7 (diagram.png)`);
 expect(result.text).toBe('Inspect these inputs');
 expect(result.refs).toEqual([
  {kind:'file',title:'src/app.js',label:'app.js'},
  {kind:'folder',title:'docs',label:'docs'},
  {kind:'message',title:'message:42',label:'msg:42'},
  {kind:'attachment',title:'attachment:7 (diagram.png)',label:'diagram.png'},
 ]);
});

test('malformed reference blocks remain editable text',()=>{
 const result=parseQueuedContent('Attachments:\n- external-url:https://example.invalid/a\n\nBody');
 expect(result.refs).toEqual([]);
 expect(result.text).toContain('external-url:https://example.invalid/a');
});
