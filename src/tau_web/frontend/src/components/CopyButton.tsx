import { useEffect, useRef, useState } from "preact/hooks";

/** Piclaw copy-button markup, with Tau-local clipboard feedback. */
export function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout>>();
  useEffect(() => () => clearTimeout(timer.current), []);
  return <button type="button" className={`tool-call__copy${copied ? " tool-call__copy--copied" : ""}`}
    title={copied ? "Copied!" : "Copy"} aria-label={copied ? "Copied!" : "Copy"}
    onClick={async (event) => {
      event.stopPropagation();
      try {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        clearTimeout(timer.current);
        timer.current = setTimeout(() => setCopied(false), 2000);
      } catch { setCopied(false); }
    }}>{copied ? "✓" : <i className="codicon codicon-copy" aria-hidden="true" />}</button>;
}
