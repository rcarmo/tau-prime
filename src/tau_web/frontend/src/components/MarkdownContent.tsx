import { useLayoutEffect, useMemo, useRef, useState } from "preact/hooks";
import { marked } from "marked";
import DOMPurify from "dompurify";

/** Sanitized core Markdown; optional Piclaw math/diagram plugins are not yet ported. */
export function MarkdownContent({ content }: { content: string }) {
  const root = useRef<HTMLDivElement>(null);
  const restoreFocus = useRef<string | null>(null);
  useLayoutEffect(() => {
    if (restoreFocus.current !== null) {
      root.current?.querySelector<HTMLButtonElement>(`[data-block-index="${restoreFocus.current}"]`)?.focus();
      restoreFocus.current = null;
    }
  });
  const [copyStatus, setCopyStatus] = useState("");
  const [expanded, setExpanded] = useState<{content: string; blocks: number[]}>({content:"",blocks:[]});
  const html = useMemo(() => {
    const clean = DOMPurify.sanitize(marked.parse(content, { async: false }), {
      USE_PROFILES: { html: true },
      FORBID_TAGS: ["style", "form", "input", "button", "iframe"],
      FORBID_ATTR: ["style"],
    });
    // Work only on detached, sanitized markup. Preact owns the mounted content.
    const template = document.createElement("template");
    template.innerHTML = clean;
    for (const [index, code] of Array.from(template.content.querySelectorAll("pre > code")).entries()) {
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
      const text = code.textContent ?? "";
      const lineCount = text.replace(/\r\n?/g, "\n").split("\n").length;
      if (lineCount > 40 || bytes.length > 24 * 1024) {
        const isExpanded = expanded.content === content && expanded.blocks.includes(index);
        block.classList.add("post-code-block-collapsed");
        if (isExpanded) block.classList.add("post-code-block-expanded");
        block.style.setProperty("--post-code-preview-lines", "16");
        const toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "post-code-expand-btn";
        toggle.dataset.blockIndex = String(index);
        toggle.setAttribute("aria-expanded", String(isExpanded));
        toggle.textContent = isExpanded ? "Collapse code" : `Expand code (${lineCount} lines, ${bytes.length} bytes)`;
        block.prepend(toggle);
      }
    }
    return template.innerHTML;
  }, [content, expanded]);
  return <><div ref={root} className="tau-markdown" onClick={async event => {
    const toggle = (event.target as Element).closest<HTMLButtonElement>("button.post-code-expand-btn");
    if (toggle && event.currentTarget.contains(toggle)) {
      const index = Number(toggle.dataset.blockIndex);
      if (document.activeElement === toggle) restoreFocus.current = String(index);
      setExpanded(previous => {
        const blocks = previous.content === content ? previous.blocks : [];
        return {content,blocks:blocks.includes(index) ? blocks.filter(value=>value!==index) : [...blocks,index]};
      });
      return;
    }
    const button = (event.target as Element).closest<HTMLButtonElement>("button.post-code-copy-btn");
    if (!button || !event.currentTarget.contains(button)) return;
    try {
      const bytes = Uint8Array.from(atob(button.dataset.code ?? ""), c => c.charCodeAt(0));
      await navigator.clipboard.writeText(new TextDecoder().decode(bytes));
      setCopyStatus("Code copied");
    } catch { setCopyStatus("Unable to copy code; try again"); }
  }} dangerouslySetInnerHTML={{ __html: html }} /><span className="sr-only" role="status" aria-label="Code clipboard status">{copyStatus}</span></>;
}
