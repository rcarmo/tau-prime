import {test, expect} from 'bun:test';
import {initialTauSession} from '../static/js/tau-session-selection.js';
const sessions=[{id:'archived',archived:true},{id:'one'},{id:'two'}];
test('selects first real active session, not a synthetic default',()=> {
    expect(initialTauSession(sessions)).toBe('one');
    expect(initialTauSession([])).toBe(null);
});
test('preserves explicit URL selection and rejects unavailable sessions',()=> {
    expect(initialTauSession(sessions,'?session=two')).toBe('two');
    expect(()=>initialTauSession(sessions,'?session=missing')).toThrow('unavailable');
    expect(()=>initialTauSession(sessions,'?session=archived')).toThrow('unavailable');
});
