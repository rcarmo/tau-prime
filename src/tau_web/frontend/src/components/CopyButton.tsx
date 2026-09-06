import { ClassicIcon } from "./ClassicIcon";
import { useEffect, useRef, useState } from "preact/hooks";

/** Piclaw copy-button markup, with Tau-local clipboard feedback. */
export function CopyButton({ text, classic = false }: { text: string; classic?: boolean }) {
  const [copied, setCopied] = useState(false);
  const [failed, setFailed] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout>>();
  useEffect(() => () => clearTimeout(timer.current), []);
  return <button type="button" className={classic ? "post-action-btn" : `tool-call__copy${copied ? " tool-call__copy--copied" : ""}`}
    title={failed ? "Copy failed — retry" : copied ? "Copied!" : "Copy"} aria-label={failed ? "Copy failed — retry" : copied ? "Copied!" : "Copy"}
    onClick={async (event) => {
      event.stopPropagation();
      setFailed(false);
      setCopied(false);
      clearTimeout(timer.current);
      try {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        clearTimeout(timer.current);
        timer.current = setTimeout(() => setCopied(false), 2000);
      } catch { setFailed(true); }
    }}>{copied ? "✓" : classic ? <ClassicIcon name="copy" /> : <i className="codicon codicon-copy" aria-hidden="true" />}</button>;
}
