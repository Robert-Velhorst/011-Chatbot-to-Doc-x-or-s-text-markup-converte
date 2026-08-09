export type InputFormat = "auto" | "markdown" | "html" | "plain";
export type OutputFormat = "docx" | "pdf" | "markdown" | "text";

export interface ProjectSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  current_version: number;
}

export interface Verification {
  artifact: string;
  status: "verified" | "unverified" | "failed";
  page_count: number | null;
  checks: string[];
  reason: string | null;
  preview_path?: string | null;
}

export interface Artifact {
  format: OutputFormat;
  name: string;
  sha256: string;
  size: number;
  verification: Verification | null;
}

export interface GenerationResult {
  project_id: string;
  version: number;
  template: TemplateProfile;
  artifacts: Artifact[];
}

export interface TemplateProfile {
  id: string;
  name: string;
  description: string;
}

export interface SourceResponse {
  project_id: string;
  version: number;
  title: string;
  source_format: Exclude<InputFormat, "auto">;
  source: string;
}
