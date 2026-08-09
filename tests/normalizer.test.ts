import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { normalizeSelection } from "../src/extension/normalizer";

interface Fixture { name: string; html: string; expectedHtml: string; plainTextIncludes: string[]; }
const fixtures = JSON.parse(readFileSync(resolve("fixtures/normalization.json"), "utf8")) as Fixture[];

describe("normalizeSelection", () => {
  for (const fixture of fixtures) {
    it(fixture.name, () => {
      const result = normalizeSelection(fixture.html);
      expect(result.html).toBe(fixture.expectedHtml);
      for (const value of fixture.plainTextIncludes) expect(result.plainText).toContain(value);
      expect(result.html).not.toMatch(/button|script|toolbar|utm_/i);
    });
  }
});
