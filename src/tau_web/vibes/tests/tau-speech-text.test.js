import {test,expect} from 'bun:test';
import {speechText} from '../static/js/tau-speech-text.js';
test('speech uses bounded readable text and omits fenced code',()=>{
 expect(speechText('# Heading\n\n[Link](https://example.com) `code`')).toBe('Heading. Link code');
 expect(speechText('```js\nsecret code\n```')).toBe('Code block omitted.');
 expect(speechText('x'.repeat(2000))).toHaveLength(1600);
});
