import { CheckCircle2, LockKeyhole, Menu, Save, TriangleAlert, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "./api";
import { Editor } from "./components/Editor";
import { Inspector } from "./components/Inspector";
import { SecondaryView } from "./components/SecondaryView";
import { Sidebar, type View } from "./components/Sidebar";
import type { Artifact, InputFormat, OutputFormat, ProjectSummary, TemplateProfile } from "./types";

const sample = `# Q2 Business Brief

This brief outlines our priorities and key initiatives for Q2.

## Objectives
- Deliver measurable customer value
- Increase operational efficiency
- Strengthen market position

### Key initiatives
1. Product improvements
   - Performance optimization
   - Reliability enhancements
2. Customer enablement
   - Documentation updates
   - Training and webinars

## Q2 targets
| Metric | Target | Owner |
| --- | --- | --- |
| Monthly active users | 125,000 | Product |
| Revenue | $2.5M | Finance |
| Net promoter score | 50 | Customer Success |

## Example code
\`\`\`javascript
function greet(name) {
  return \"Hello, \" + name + \"!\";
}
console.log(greet(\"AI Clean Paste\"));
\`\`\``;

export default function App() {
  const [view, setView] = useState<View>("studio");
  const [menuOpen, setMenuOpen] = useState(false);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [templates, setTemplates] = useState<TemplateProfile[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [activeVersion, setActiveVersion] = useState<number | null>(null);
  const [title, setTitle] = useState("Q2 Business Brief");
  const [source, setSource] = useState(sample);
  const [inputFormat, setInputFormat] = useState<InputFormat>("auto");
  const [templateId, setTemplateId] = useState("standard_business_brief");
  const [formats, setFormats] = useState<OutputFormat[]>(["docx", "pdf", "markdown", "text"]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [dirty, setDirty] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [notice, setNotice] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [locked, setLocked] = useState(false);
  const [accessToken, setAccessToken] = useState("");

  const refreshProjects = useCallback(async () => {
    const result = await api.projects();
    setProjects(result);
  }, []);

  useEffect(() => {
    Promise.all([api.templates(), api.projects()])
      .then(([templateResult, projectResult]) => {
        setTemplates(templateResult);
        setProjects(projectResult);
      })
      .catch((error: Error) => {
        if (error instanceof ApiError && error.status === 401) setLocked(true);
        else setNotice({ type: "error", message: error.message });
      });
  }, []);

  async function unlock(event: React.FormEvent) {
    event.preventDefault();
    try {
      await api.unlock(accessToken);
      const [templateResult, projectResult] = await Promise.all([api.templates(), api.projects()]);
      setTemplates(templateResult);
      setProjects(projectResult);
      setAccessToken("");
      setLocked(false);
    } catch (error) {
      setNotice({ type: "error", message: (error as Error).message });
    }
  }

  function editTitle(value: string) {
    setTitle(value);
    setDirty(true);
  }

  function editSource(value: string) {
    setSource(value);
    setDirty(true);
    setArtifacts([]);
  }

  function editFormat(value: InputFormat) {
    setInputFormat(value);
    setDirty(true);
  }

  function newDocument() {
    setActiveProjectId(null);
    setActiveVersion(null);
    setTitle("Untitled document");
    setSource("");
    setInputFormat("auto");
    setArtifacts([]);
    setDirty(true);
    setView("studio");
    setMenuOpen(false);
    setNotice(null);
  }

  async function openProject(project: ProjectSummary) {
    try {
      const response = await api.source(project.id);
      setActiveProjectId(project.id);
      setActiveVersion(response.version);
      setTitle(response.title);
      setSource(response.source);
      setInputFormat(response.source_format);
      setArtifacts([]);
      setDirty(false);
      setView("studio");
      setMenuOpen(false);
      setNotice(null);
    } catch (error) {
      setNotice({ type: "error", message: (error as Error).message });
    }
  }

  async function deleteProject(project: ProjectSummary) {
    if (!window.confirm(`Delete “${project.title}” and all of its local versions? This cannot be undone.`)) return;
    try {
      await api.remove(project.id);
      if (activeProjectId === project.id) newDocument();
      await refreshProjects();
      setNotice({ type: "success", message: "The local project was deleted." });
    } catch (error) {
      setNotice({ type: "error", message: (error as Error).message });
    }
  }

  async function generate() {
    if (!title.trim() || !source.trim()) {
      setNotice({ type: "error", message: "Add a title and source text before generating files." });
      return;
    }
    setGenerating(true);
    setNotice(null);
    try {
      let projectId = activeProjectId;
      let version = activeVersion;
      if (!projectId) {
        const created = await api.create(title.trim(), source, inputFormat);
        projectId = created.id;
        version = created.current_version;
        setActiveProjectId(projectId);
      } else if (dirty) {
        const corrected = await api.correct(projectId, title.trim(), source, inputFormat);
        version = corrected.current_version;
      }
      const result = await api.generate(projectId, formats, templateId);
      setActiveVersion(result.version ?? version);
      setArtifacts(result.artifacts);
      setDirty(false);
      await refreshProjects();
      const problems = result.artifacts.filter((artifact) => artifact.verification?.status === "failed");
      setNotice(
        problems.length
          ? { type: "error", message: "Files were created, but at least one verification check failed." }
          : { type: "success", message: "Files generated locally. Verification results are shown at right." },
      );
    } catch (error) {
      setNotice({ type: "error", message: (error as Error).message });
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="app-shell">
      <button className="mobile-menu" type="button" onClick={() => setMenuOpen((current) => !current)} aria-label="Toggle navigation">
        {menuOpen ? <X /> : <Menu />}
      </button>
      <div className={menuOpen ? "sidebar-wrap open" : "sidebar-wrap"}>
        <Sidebar
          projects={projects}
          activeProjectId={activeProjectId}
          view={view}
          onView={(next) => { setView(next); setMenuOpen(false); }}
          onNew={newDocument}
          onOpen={openProject}
        />
      </div>

      {view === "studio" ? (
        <>
          <Editor
            title={title}
            source={source}
            inputFormat={inputFormat}
            onTitle={editTitle}
            onSource={editSource}
            onFormat={editFormat}
          />
          <Inspector
            projectId={activeProjectId}
            version={activeVersion}
            templates={templates}
            templateId={templateId}
            formats={formats}
            artifacts={artifacts}
            generating={generating}
            onTemplate={setTemplateId}
            onFormats={setFormats}
            onGenerate={generate}
          />
        </>
      ) : (
        <SecondaryView view={view} projects={projects} templates={templates} onOpen={openProject} onDelete={deleteProject} />
      )}

      <footer className="status-bar">
        <span><LockKeyhole size={15} /> Stored locally</span>
        <span className={dirty ? "dirty" : "saved"}>
          {dirty ? <Save size={15} /> : <CheckCircle2 size={15} />}
          {dirty ? "Changes save when files are generated" : "All changes saved"}
        </span>
      </footer>

      {notice ? (
        <div className={`notice ${notice.type}`} role="status">
          {notice.type === "success" ? <CheckCircle2 size={19} /> : <TriangleAlert size={19} />}
          <span>{notice.message}</span>
          <button type="button" aria-label="Dismiss message" onClick={() => setNotice(null)}><X size={17} /></button>
        </div>
      ) : null}

      {locked ? (
        <div className="auth-backdrop" role="dialog" aria-modal="true" aria-labelledby="auth-title">
          <form className="auth-dialog" onSubmit={unlock}>
            <LockKeyhole size={27} />
            <h2 id="auth-title">Unlock local workspace</h2>
            <p>Enter the access token configured on this computer. It is exchanged for an HTTP-only local session and is not stored by the interface.</p>
            <label className="field"><span>Access token</span><input type="password" autoFocus value={accessToken} onChange={(event) => setAccessToken(event.target.value)} /></label>
            <button className="generate" type="submit" disabled={!accessToken}>Unlock</button>
          </form>
        </div>
      ) : null}
    </div>
  );
}
