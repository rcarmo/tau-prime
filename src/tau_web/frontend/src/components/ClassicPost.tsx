import type { ComponentChildren } from "preact";

/** Classic post.ts hierarchy, with Tau-owned identity/content/actions. */
export function ClassicPost({ id, agent, author, time, avatar, actions, children }: {
  id: string;
  agent: boolean;
  author: string;
  time: string;
  avatar: ComponentChildren;
  actions?: ComponentChildren;
  children: ComponentChildren;
}) {
  return <article id={id} className={`post${agent ? " agent-post" : ""}`}>
    <div className={`post-avatar${agent ? " agent-avatar" : ""}`} aria-hidden="true">{avatar}</div>
    <div className="post-body">
      {actions && <div className="post-actions">{actions}</div>}
      <div className="post-meta">
        <span className="post-author">{author}</span>
        <span className="post-time">{time}</span>
      </div>
      <div className="post-content">{children}</div>
    </div>
  </article>;
}
