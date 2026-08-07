import { render } from "preact";

function PreactShellPlaceholder() {
  return <span hidden data-tau-preact-shell-ready="true">Tau Preact shell placeholder</span>;
}

const mount = document.querySelector<HTMLElement>("[data-tau-preact-shell]");

if (mount !== null) {
  render(<PreactShellPlaceholder />, mount);
}
