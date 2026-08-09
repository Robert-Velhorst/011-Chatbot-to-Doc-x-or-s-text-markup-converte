import type { ProviderAdapter, ProviderId } from "./types";

const host = (...suffixes: string[]) => (hostname: string) =>
  suffixes.some((suffix) => hostname === suffix || hostname.endsWith(`.${suffix}`));

export const PROVIDERS: readonly ProviderAdapter[] = [
  {
    id: "chatgpt",
    label: "ChatGPT",
    hostMatches: host("chatgpt.com", "chat.openai.com"),
    responseSelectors: ["[data-message-author-role='assistant']", "article[data-testid*='conversation-turn']"]
  },
  {
    id: "claude",
    label: "Claude",
    hostMatches: host("claude.ai"),
    responseSelectors: ["[data-is-streaming]", "[data-testid*='assistant']", ".font-claude-message"]
  },
  {
    id: "gemini",
    label: "Gemini",
    hostMatches: host("gemini.google.com"),
    responseSelectors: ["message-content", ".model-response-text", "[data-message-author='model']"]
  },
  {
    id: "copilot",
    label: "Copilot",
    hostMatches: host("copilot.microsoft.com"),
    responseSelectors: ["[data-testid*='assistant']", "cib-message-group[author='bot']", "[data-author='bot']"]
  },
  {
    id: "perplexity",
    label: "Perplexity",
    hostMatches: host("perplexity.ai"),
    responseSelectors: ["[data-testid*='answer']", ".prose", "[class*='answer']"]
  },
  {
    id: "grok",
    label: "Grok",
    hostMatches: host("grok.com", "x.com"),
    responseSelectors: ["[data-testid*='assistant']", "[class*='response']", ".prose"]
  },
  {
    id: "manus",
    label: "Manus",
    hostMatches: host("manus.im", "manus.space"),
    responseSelectors: ["[data-testid*='assistant']", "[class*='message-content']", ".prose"]
  }
];

export const PROVIDER_IDS = PROVIDERS.map((provider) => provider.id) as ProviderId[];

export function providerForHost(hostname: string): ProviderAdapter | undefined {
  return PROVIDERS.find((provider) => provider.hostMatches(hostname));
}

export function closestResponseContainer(node: Node | null, provider: ProviderAdapter): Element | null {
  const start = node?.nodeType === Node.ELEMENT_NODE ? (node as Element) : node?.parentElement;
  if (!start) return null;
  for (const selector of provider.responseSelectors) {
    try {
      const result = start.closest(selector);
      if (result) return result;
    } catch {
      // An obsolete provider selector must never break native copying.
    }
  }
  return null;
}
