import { Check, Download, FileArchive, FileCode2, FileText, FileType2, LoaderCircle, ShieldCheck, TriangleAlert } from "lucide-react";
import { artifactUrl, exportUrl } from "../api";
import type { Artifact, OutputFormat, TemplateProfile } from "../types";

interface InspectorProps {
  projectId: string | null;
  version: number | null;
  templates: TemplateProfile[];
  templateId: string;
  formats: OutputFormat[];
  artifacts: Artifact[];
  generating: boolean;
  onTemplate: (value: string) => void;
  onFormats: (value: OutputFormat[]) => void;
  onGenerate: () => void;
}

const formatOptions: Array<{ value: OutputFormat; label: string; extension: string }> = [
  { value: "docx", label: "DOCX", extension: ".docx" },
  { value: "pdf", label: "PDF", extension: ".pdf" },
  { value: "markdown", label: "Markdown", extension: ".md" },
  { value: "text", label: "Plain text", extension: ".txt" },
];

function formatSize(size: number) {
  if (size < 1024) return `${size} B`;
  return `${Math.round(size / 1024)} KB`;
}

function FileIcon({ format }: { format: OutputFormat }) {
  if (format === "markdown") return <FileCode2 size={18} />;
  if (format === "text") return <FileText size={18} />;
  return <FileType2 size={18} />;
}

export function Inspector(props: InspectorProps) {
  const verifications = props.artifacts.filter((artifact) => artifact.verification);
  function toggleFormat(value: OutputFormat) {
    props.onFormats(
      props.formats.includes(value)
        ? props.formats.filter((current) => current !== value)
        : [...props.formats, value],
    );
  }

  return (
    <aside className="inspector" aria-label="Output settings">
      <section className="inspector-section output-settings">
        <h2>Output</h2>
        <label className="field">
          <span>Template</span>
          <select value={props.templateId} onChange={(event) => props.onTemplate(event.target.value)}>
            {props.templates.map((template) => <option key={template.id} value={template.id}>{template.name}</option>)}
          </select>
        </label>
        <fieldset className="formats">
          <legend>Formats</legend>
          {formatOptions.map((format) => (
            <label key={format.value}>
              <input
                type="checkbox"
                checked={props.formats.includes(format.value)}
                onChange={() => toggleFormat(format.value)}
              />
              <span>{format.label}</span>
              <small>{format.extension}</small>
            </label>
          ))}
        </fieldset>
        <button
          type="button"
          className="generate"
          disabled={props.generating || props.formats.length === 0}
          onClick={props.onGenerate}
        >
          {props.generating ? <LoaderCircle className="spin" size={18} /> : null}
          {props.generating ? "Generating…" : "Generate files"}
        </button>
      </section>

      <section className="inspector-section verification">
        <h2>Verification</h2>
        {verifications.length === 0 ? (
          <div className="empty-state">
            <ShieldCheck size={20} />
            <span>Generate DOCX or PDF to run verification.</span>
          </div>
        ) : verifications.map((artifact) => {
          const verification = artifact.verification!;
          const verified = verification.status === "verified";
          const failed = verification.status === "failed";
          return (
            <div className={`verification-row ${verification.status}`} key={artifact.format} title={verification.reason || verification.checks.join("\n")}>
              {failed ? <TriangleAlert size={19} /> : <Check size={19} />}
              <div>
                <strong>{artifact.format.toUpperCase()}</strong>
                <small>{verification.page_count ? `${verification.page_count} page${verification.page_count === 1 ? "" : "s"}` : verification.checks.at(-1)}</small>
              </div>
              <span>{verified ? "Verified" : failed ? "Failed" : "Structural"}</span>
            </div>
          );
        })}
      </section>

      <section className="inspector-section files">
        <div className="section-heading">
          <h2>Files</h2>
          {props.projectId && props.version && props.artifacts.length > 0 ? (
            <a className="export-link" href={exportUrl(props.projectId, props.version)} title="Export source, files, and checksum manifest">
              <FileArchive size={16} /> Export
            </a>
          ) : null}
        </div>
        {props.artifacts.length === 0 ? (
          <p className="file-empty">Generated files stay in this local workspace.</p>
        ) : props.artifacts.map((artifact) => (
          <div className={`file-row file-${artifact.format}`} key={artifact.format}>
            <FileIcon format={artifact.format} />
            <div>
              <strong>{artifact.name}</strong>
              <small>{formatSize(artifact.size)}</small>
            </div>
            <a
              href={artifactUrl(props.projectId!, props.version!, artifact.name)}
              download={artifact.name}
              title={`Download ${artifact.name}`}
              aria-label={`Download ${artifact.name}`}
            >
              <Download size={17} />
            </a>
          </div>
        ))}
      </section>
    </aside>
  );
}
