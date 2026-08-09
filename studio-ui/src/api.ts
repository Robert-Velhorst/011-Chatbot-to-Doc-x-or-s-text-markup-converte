import type { GenerationResult, InputFormat, OutputFormat, ProjectSummary, SourceResponse, TemplateProfile } from "./types";

const jsonHeaders = { "Content-Type": "application/json" };

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { ...init, headers: { ...jsonHeaders, ...init?.headers } });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(body.detail || `Request failed with ${response.status}`, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  unlock: (token: string) => request<{ status: string }>("/api/session", { method: "POST", body: JSON.stringify({ token }) }),
  templates: () => request<TemplateProfile[]>("/api/templates"),
  projects: () => request<ProjectSummary[]>("/api/projects"),
  source: (projectId: string) => request<SourceResponse>(`/api/projects/${projectId}/source`),
  create: (title: string, source: string, sourceFormat: InputFormat) =>
    request<ProjectSummary>("/api/projects", {
      method: "POST",
      body: JSON.stringify({ title, source, source_format: sourceFormat }),
    }),
  correct: (projectId: string, title: string, source: string, sourceFormat: InputFormat) =>
    request<ProjectSummary>(`/api/projects/${projectId}/versions`, {
      method: "POST",
      body: JSON.stringify({ title, source, source_format: sourceFormat }),
    }),
  generate: (projectId: string, formats: OutputFormat[], templateId: string) =>
    request<GenerationResult>(`/api/projects/${projectId}/generate`, {
      method: "POST",
      body: JSON.stringify({ formats, template_id: templateId }),
    }),
  remove: (projectId: string) => request<void>(`/api/projects/${projectId}`, { method: "DELETE" }),
};

export function artifactUrl(projectId: string, version: number, name: string): string {
  return `/api/projects/${projectId}/versions/${version}/artifacts/${encodeURIComponent(name)}`;
}

export function exportUrl(projectId: string, version: number): string {
  return `/api/projects/${projectId}/export?version=${version}`;
}
