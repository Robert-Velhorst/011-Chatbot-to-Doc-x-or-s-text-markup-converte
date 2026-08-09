import { Clock3, FileText, History, LayoutTemplate, Plus, Settings, SquarePen } from "lucide-react";
import type { ProjectSummary } from "../types";

export type View = "studio" | "templates" | "history" | "settings";

interface SidebarProps {
  projects: ProjectSummary[];
  activeProjectId: string | null;
  view: View;
  onView: (view: View) => void;
  onNew: () => void;
  onOpen: (project: ProjectSummary) => void;
}

const nav = [
  { id: "studio" as const, label: "Studio", icon: SquarePen },
  { id: "templates" as const, label: "Templates", icon: LayoutTemplate },
  { id: "history" as const, label: "History", icon: History },
  { id: "settings" as const, label: "Settings", icon: Settings },
];

export function Sidebar({ projects, activeProjectId, view, onView, onNew, onOpen }: SidebarProps) {
  return (
    <aside className="sidebar" aria-label="Primary navigation">
      <header className="brand">
        <span className="brand-mark" aria-hidden="true">A</span>
        <div>
          <strong>AI Clean Paste</strong>
          <span>Document Studio</span>
        </div>
      </header>

      <button className="new-document" type="button" onClick={onNew}>
        <Plus size={20} strokeWidth={1.8} />
        New document
      </button>

      <section className="recent" aria-labelledby="recent-heading">
        <h2 id="recent-heading">Recent documents</h2>
        <div className="recent-list">
          {projects.length === 0 ? (
            <p className="recent-empty">Your local documents appear here.</p>
          ) : (
            projects.slice(0, 5).map((project) => (
              <button
                type="button"
                key={project.id}
                className={project.id === activeProjectId ? "recent-item active" : "recent-item"}
                onClick={() => onOpen(project)}
                title={project.title}
              >
                <FileText size={17} strokeWidth={1.7} />
                <span>{project.title}</span>
              </button>
            ))
          )}
        </div>
      </section>

      <nav className="main-nav">
        {nav.map(({ id, label, icon: Icon }) => (
          <button
            type="button"
            key={id}
            className={view === id ? "nav-item active" : "nav-item"}
            onClick={() => onView(id)}
          >
            <Icon size={20} strokeWidth={1.7} />
            {label}
          </button>
        ))}
      </nav>

      <footer className="sidebar-footer">
        <Clock3 size={15} />
        Local workspace
      </footer>
    </aside>
  );
}
