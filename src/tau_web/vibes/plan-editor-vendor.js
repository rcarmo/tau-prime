// Separate self-contained CodeMirror graph: never mix extensions from the legacy bundle.
export {EditorState,Compartment,RangeSetBuilder} from '@codemirror/state';
export {EditorView,ViewPlugin,Decoration} from '@codemirror/view';
export {markdown} from '@codemirror/lang-markdown';
export {minimalSetup} from 'codemirror';
export {githubDark,githubLight} from '@uiw/codemirror-theme-github';
