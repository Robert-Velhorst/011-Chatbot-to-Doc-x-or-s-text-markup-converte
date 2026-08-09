import { ExternalLink, FileClock, HardDrive, LockKeyhole, Trash2 } from "lucide-react";
import type { ProjectSummary, TemplateProfile } from "../types";
import type { View } from "./Sidebar";

interface SecondaryViewProps {
  view: Exclude<View, "studio">;
  projects: ProjectSummary[];
  templates: TemplateProfile[];
  onOpen: (project: ProjectSummary) => void;
  onDelete: (project: ProjectSummary) => void;
}

export function SecondaryView({ view, projects, templates, onOpen, onDelete }: SecondaryViewProps) {
  if (view === "templates") {
    return (
      <main className="secondary-view">
        <h1>Templates</h1>
        <p className="lede">Choose a portable document system. Templates control typography, spacing, tables, and page geometry.</p>
        <div className="template-list">
          {templates.map((template) => (
            <article key={template.id}>
              <div className="template-sheet" aria-hidden="true"><span /><span /><span /><span /></div>
              <div><h2>{template.name}</h2><p>{template.description}</p></div>
            </article>
          ))}
        </div>
      </main>
    );
  }
  if (view === "history") {
    return (
      <main className="secondary-view">
        <h1>History</h1>
        <p className="lede">Each correction creates an immutable local version. Generated files remain attached to their source version.</p>
        <div className="history-table" role="table" aria-label="Document history">
          {projects.length === 0 ? <p>No local documents yet.</p> : projects.map((project) => (
            <div className="history-row" role="row" key={project.id}>
              <FileClock size={20} />
              <button type="button" onClick={() => onOpen(project)}>
                <strong>{project.title}</strong>
                <span>Version {project.current_version} · Updated {new Date(project.updated_at).toLocaleString()}</span>
              </button>
              <button type="button" className="delete" onClick={() => onDelete(project)} aria-label={`Delete ${project.title}`}><Trash2 size={18} /></button>
            </div>
          ))}
        </div>
      </main>
    );
  }
  return (
    <main className="secondary-view">
      <h1>Settings</h1>
      <p className="lede">Privacy and operational boundaries are fixed by design.</p>
      <div className="settings-list">
        <article><HardDrive size={22} /><div><h2>Local storage</h2><p>Source versions, artifacts, and settings stay on this computer. Export packages include checksums.</p></div></article>
        <article><LockKeyhole size={22} /><div><h2>No content telemetry</h2><p>No cloud processing, copied-content logs, clipboard history, analytics, or global keyboard hooks.</p></div></article>
        <article><ExternalLink size={22} /><div><h2>Loopback server</h2><p>The default server listens only on 127.0.0.1. A token is mandatory for production mode or non-loopback binding.</p></div></article>
      </div>
    </main>
  );
}
