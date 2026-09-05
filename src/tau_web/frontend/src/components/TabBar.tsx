// Markup adapted from Piclaw 2.15.3 TabBar.tsx (MIT; see PICLAW-LICENSE.md).
// Tau currently exposes one central chat view; do not invent unsupported tabs.
export function TabBar() {
  return (
    <div className="tab-bar" role="tablist" aria-label="Central pane tabs">
      <button
        role="tab"
        type="button"
        aria-selected={true}
        className="tab-bar__tab tab-bar__tab--active"
      >
        <span className="tab-bar__tab__label">Chat</span>
      </button>
    </div>
  );
}
