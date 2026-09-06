import { useMemo, useState } from "preact/hooks";
import { marked } from "marked";
import DOMPurify from "dompurify";

/** Sanitized core Markdown; optional Piclaw math/diagram plugins are not yet ported. */
export function MarkdownContent({ content }: { content: string }) {
  const [copyStatus, setCopyStatus] = useState("");
  const html = useMemo(() => {
    const clean = DOMPurify.sanitize(marked.parse(content, { async: false }), {
      USE_PROFILES: { html: true },
      FORBID_TAGS: ["style", "form", "input", "button", "iframe"],
      FORBID_ATTR: ["style"],
    });
    // Work only on detached, sanitized markup. Preact owns the mounted content.
    const template = document.createElement("template");
    template.innerHTML = clean;
    for (const code of Array.from(template.content.querySelectorAll("pre > code"))) {
      const pre = code.parentElement!;
      const language = Array.from(code.classList).find(c => c.startsWith("language-"))?.slice(9) ?? "";
      code.className = `hljs${language ? ` language-${language}` : ""}`;
      const block = document.createElement("div");
      block.className = "post-code-block";
      const button = document.createElement("button");
      button.className = "post-code-copy-btn";
      button.type = "button";
      button.setAttribute("aria-label", "Copy code");
      const bytes = new TextEncoder().encode(code.textContent ?? "");
      button.dataset.code = btoa(Array.from(bytes, byte => String.fromCharCode(byte)).join(""));
      button.textContent = "Copy";
      pre.replaceWith(block);
      block.append(pre, button);
    }
    return template.innerHTML;
  }, [content]);
  return <><div className="tau-markdown" onClick={async event => {
    const button = (event.target as Element).closest<HTMLButtonElement>("button.post-code-copy-btn");
    if (!button || !event.currentTarget.contains(button)) return;
    try {
      const bytes = Uint8Array.from(atob(button.dataset.code ?? ""), c => c.charCodeAt(0));
      await navigator.clipboard.writeText(new TextDecoder().decode(bytes));
      setCopyStatus("Code copied");
    } catch { setCopyStatus("Unable to copy code; try again"); }
  }} dangerouslySetInnerHTML={{ __html: html }} /><span className="sr-only" role="status" aria-label="Code clipboard status">{copyStatus}</span></>;
}
