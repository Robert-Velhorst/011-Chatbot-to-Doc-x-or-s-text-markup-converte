import { describe, expect, it } from "vitest";
import { PROVIDERS, providerForHost } from "../src/extension/providers";

describe("provider registry", () => {
  it("recognizes every advertised provider", () => {
    expect(providerForHost("chatgpt.com")?.id).toBe("chatgpt");
    expect(providerForHost("claude.ai")?.id).toBe("claude");
    expect(providerForHost("gemini.google.com")?.id).toBe("gemini");
    expect(providerForHost("copilot.microsoft.com")?.id).toBe("copilot");
    expect(providerForHost("www.perplexity.ai")?.id).toBe("perplexity");
    expect(providerForHost("grok.com")?.id).toBe("grok");
    expect(providerForHost("app.manus.im")?.id).toBe("manus");
    expect(PROVIDERS).toHaveLength(7);
  });

  it("does not classify unrelated websites", () => {
    expect(providerForHost("example.com")).toBeUndefined();
  });
});
