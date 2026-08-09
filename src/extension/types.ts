export type ProviderId =
  | "chatgpt"
  | "claude"
  | "gemini"
  | "copilot"
  | "perplexity"
  | "grok"
  | "manus";

export interface ProviderAdapter {
  id: ProviderId;
  label: string;
  hostMatches(hostname: string): boolean;
  responseSelectors: readonly string[];
}

export interface ClipboardPayload {
  html: string;
  plainText: string;
}

export interface CleanPasteSettings {
  enabled: boolean;
  providers: Record<ProviderId, boolean>;
  genericOrigins: string[];
}
