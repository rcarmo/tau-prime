import { Fragment, render } from "preact";
import appShellMarkup from "./app-shell.html";

/** Preact-owned Tau shell. Regions remain DOM-compatible while they are
 * incrementally replaced by typed components. */
function TauShell() {
  return (
    <Fragment>
      <a className="skip-link" href="#timeline-main">Skip to timeline</a>
      <div className="app-shell" dangerouslySetInnerHTML={{ __html: appShellMarkup }} />
      <button
        id="drawer-backdrop"
        className="drawer-backdrop"
        type="button"
        hidden
        aria-label="Close open drawers"
      />
      <noscript><p className="noscript-banner">Tau Web Shell requires JavaScript to load persisted sessions.</p></noscript>
    </Fragment>
  );
}

const mount = document.getElementById("app");
if (!mount) throw new Error("Missing #app root element");
render(<TauShell />, mount);
