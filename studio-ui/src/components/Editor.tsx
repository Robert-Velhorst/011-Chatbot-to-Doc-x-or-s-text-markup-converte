import { Maximize2 } from "lucide-react";
import type { InputFormat } from "../types";

interface EditorProps {
  title: string;
  source: string;
  inputFormat: InputFormat;
  onTitle: (value: string) => void;
  onSource: (value: string) => void;
  onFormat: (value: InputFormat) => void;
}

const formats: Array<{ value: InputFormat; label: string }> = [
  { value: "auto", label: "Auto" },
  { value: "markdown", label: "Markdown" },
  { value: "html", label: "HTML" },
  { value: "plain", label: "Plain text" },
];

export function Editor({ title, source, inputFormat, onTitle, onSource, onFormat }: EditorProps) {
  const lineCount = Math.max(1, source.split("\n").length);
  return (
    <main className="workspace">
      <h1>Document Studio</h1>
      <div className="document-controls">
        <label className="field title-field">
          <span>Document title</span>
          <input value={title} maxLength={180} onChange={(event) => onTitle(event.target.value)} />
        </label>
        <fieldset className="format-field">
          <legend>Input format</legend>
          <div className="segmented-control">
            {formats.map((format) => (
              <button
                type="button"
                key={format.value}
                className={inputFormat === format.value ? "selected" : ""}
                onClick={() => onFormat(format.value)}
              >
                {format.label}
              </button>
            ))}
          </div>
        </fieldset>
      </div>

      <section className="editor-shell" aria-label="Source editor">
        <button className="maximize" type="button" title="Editor uses the available workspace" aria-label="Editor fills available workspace">
          <Maximize2 size={15} />
        </button>
        <div className="line-numbers" aria-hidden="true">
          {Array.from({ length: lineCount }, (_, index) => <span key={index}>{index + 1}</span>)}
        </div>
        <textarea
          spellCheck={false}
          aria-label="Document source"
          value={source}
          onChange={(event) => onSource(event.target.value)}
          placeholder="Paste chatbot output, Markdown, HTML, or plain text here…"
        />
      </section>
    </main>
  );
}
