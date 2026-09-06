import { useMemo } from "preact/hooks";
import { marked } from "marked";
import DOMPurify from "dompurify";

const labels: Record<string, string> = { js: "JavaScript", javascript: "JavaScript", ts: "TypeScript", typescript: "TypeScript", py: "Python", python: "Python", sh: "Shell", bash: "Bash", json: "JSON", go: "Go", css: "CSS", html: "HTML" };

/** Sanitized core Markdown; optional Piclaw math/diagram plugins are not yet ported. */
export function MarkdownContent({ content }: { content: string }) {
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
      block.className = "code-block";
      const header = document.createElement("div");
      header.className = "code-block__header";
      const label = document.createElement("span");
      label.className = "code-block__lang";
      label.textContent = labels[language.toLowerCase()] || language || "Text";
      const button = document.createElement("button");
      button.className = "code-block__copy";
      button.setAttribute("aria-label", "Copy code");
      const bytes = new TextEncoder().encode(code.textContent ?? "");
      button.dataset.code = btoa(Array.from(bytes, byte => String.fromCharCode(byte)).join(""));
      const icon = document.createElement("i");
      icon.className = "codicon codicon-copy";
      button.append(icon);
      header.append(label, button);
      pre.replaceWith(block);
      block.append(header, pre);
    }
    return template.innerHTML;
  }, [content]);
  return <div className="message-list__content" onClick={async event => {
    const button = (event.target as Element).closest<HTMLButtonElement>("button.code-block__copy");
    if (!button || !event.currentTarget.contains(button)) return;
    try {
      const bytes = Uint8Array.from(atob(button.dataset.code ?? ""), c => c.charCodeAt(0));
      await navigator.clipboard.writeText(new TextDecoder().decode(bytes));
    } catch { /* Clipboard permissions may be denied; never claim success. */ }
  }} dangerouslySetInnerHTML={{ __html: html }} />;
}
