import { beforeAll, describe, expect, it } from "vitest";

type ClipboardRecorder = { data: Record<string, string>; setData(type: string, value: string): void };

const recorder = (): ClipboardRecorder => ({
  data: {},
  setData(type, value) { this.data[type] = value; }
});

beforeAll(() => {
  Object.assign(globalThis, {
    chrome: {
      storage: {
        local: { get: async () => ({ settings: undefined }) },
        onChanged: { addListener: () => undefined }
      }
    }
  });
});

describe("source-side copy pipeline", () => {
  it("replaces a supported assistant copy synchronously with HTML and plain text", async () => {
    const { installCopyCleaner } = await import("../src/extension/content-core");
    installCopyCleaner("provider");
    document.body.innerHTML = "<article data-message-author-role='assistant'><p id='response'>Hello <strong>world</strong></p></article>";
    const text = document.querySelector("#response")!.firstChild!;
    const range = document.createRange();
    range.selectNodeContents(document.querySelector("#response")!);
    const selection = window.getSelection()!;
    selection.removeAllRanges();
    selection.addRange(range);
    const copied = recorder();
    const event = new Event("copy", { bubbles: true, cancelable: true });
    Object.defineProperty(event, "clipboardData", { value: copied });

    document.dispatchEvent(event);

    expect(text.textContent).toBe("Hello ");
    expect(event.defaultPrevented).toBe(true);
    expect(copied.data["text/html"]).toBe("<p>Hello <strong>world</strong></p>");
    expect(copied.data["text/plain"]).toBe("Hello world");
  });

  it("does not interfere with non-response copies", () => {
    document.body.innerHTML = "<p id='ordinary'>Keep this native</p>";
    const range = document.createRange();
    range.selectNodeContents(document.querySelector("#ordinary")!);
    const selection = window.getSelection()!;
    selection.removeAllRanges();
    selection.addRange(range);
    const copied = recorder();
    const event = new Event("copy", { bubbles: true, cancelable: true });
    Object.defineProperty(event, "clipboardData", { value: copied });

    document.dispatchEvent(event);

    expect(event.defaultPrevented).toBe(false);
    expect(copied.data).toEqual({});
  });
});
