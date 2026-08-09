import { normalizeSelection } from "./normalizer";
import { closestResponseContainer, providerForHost } from "./providers";
import { DEFAULT_SETTINGS, mergeSettings } from "./settings";
import type { CleanPasteSettings } from "./types";

type Mode = "provider" | "generic";

const SEMANTIC_BLOCKS = new Set(["P", "H1", "H2", "H3", "H4", "H5", "H6", "UL", "OL", "BLOCKQUOTE", "PRE", "TABLE"]);

function cloneSelectedMarkup(range: Range): HTMLDivElement {
  const wrapper = document.createElement("div");
  const root = range.commonAncestorContainer.nodeType === Node.ELEMENT_NODE
    ? range.commonAncestorContainer as Element
    : range.commonAncestorContainer.parentElement;
  const selectsWholeRoot = root
    && SEMANTIC_BLOCKS.has(root.tagName)
    && range.startContainer === root
    && range.startOffset === 0
    && range.endContainer === root
    && range.endOffset === root.childNodes.length;
  wrapper.appendChild(selectsWholeRoot ? root.cloneNode(true) : range.cloneContents());
  return wrapper;
}

export function installCopyCleaner(mode: Mode): void {
  let settings: CleanPasteSettings = DEFAULT_SETTINGS;
  void chrome.storage.local.get("settings").then(({ settings: stored }) => {
    settings = mergeSettings(stored as Partial<CleanPasteSettings> | undefined);
  });
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === "local" && changes.settings) settings = mergeSettings(changes.settings.newValue as Partial<CleanPasteSettings>);
  });

  document.addEventListener("copy", (event) => {
    if (!settings.enabled || !event.clipboardData) return;
    const selection = window.getSelection();
    if (!selection?.rangeCount || selection.isCollapsed) return;

    const provider = providerForHost(location.hostname);
    if (mode === "provider") {
      if (!provider || !settings.providers[provider.id]) return;
      if (!closestResponseContainer(selection.anchorNode, provider) && !closestResponseContainer(selection.focusNode, provider)) return;
    } else if (!settings.genericOrigins.includes(location.origin)) {
      return;
    }

    try {
      const range = selection.getRangeAt(0);
      const wrapper = cloneSelectedMarkup(range);
      const payload = normalizeSelection(wrapper.innerHTML);
      if (!payload.html || !payload.plainText) return;
      event.preventDefault();
      event.clipboardData.setData("text/html", payload.html);
      event.clipboardData.setData("text/plain", payload.plainText);
    } catch {
      // Preserve the browser's original copy operation if anything unexpected occurs.
    }
  }, true);
}
