import { PROVIDERS } from "./providers";
import { getSettings, saveSettings } from "./settings";
import type { CleanPasteSettings } from "./types";

const enabled = document.querySelector<HTMLInputElement>("#enabled")!;
const providers = document.querySelector<HTMLDivElement>("#providers")!;
const siteName = document.querySelector<HTMLParagraphElement>("#site-name")!;
const genericToggle = document.querySelector<HTMLButtonElement>("#generic-toggle")!;
const status = document.querySelector<HTMLParagraphElement>("#status")!;
let settings: CleanPasteSettings;
let currentOrigin: string | null = null;

function showError(message: string): void { status.textContent = message; }

function render(): void {
  enabled.checked = settings.enabled;
  providers.replaceChildren(...PROVIDERS.map((provider) => {
    const row = document.createElement("label");
    row.className = "switch-row";
    const label = document.createElement("span");
    label.textContent = provider.label;
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = settings.providers[provider.id];
    input.addEventListener("change", async () => {
      settings.providers[provider.id] = input.checked;
      await saveSettings(settings);
    });
    const visual = document.createElement("span");
    visual.className = "switch";
    row.append(label, input, visual);
    return row;
  }));
  if (currentOrigin) {
    const active = settings.genericOrigins.includes(currentOrigin);
    genericToggle.textContent = active ? "Disable generic formatting" : "Enable generic formatting";
  }
}

enabled.addEventListener("change", async () => {
  settings.enabled = enabled.checked;
  await saveSettings(settings);
});

genericToggle.addEventListener("click", async () => {
  if (!currentOrigin) return;
  const active = settings.genericOrigins.includes(currentOrigin);
  const originPattern = `${currentOrigin}/*`;
  try {
    if (!active) {
      const granted = await chrome.permissions.request({ origins: [originPattern] });
      if (!granted) return;
      const response = await chrome.runtime.sendMessage({ type: "ENABLE_GENERIC_ORIGIN", origin: currentOrigin });
      if (!response?.ok) throw new Error();
    } else {
      const response = await chrome.runtime.sendMessage({ type: "DISABLE_GENERIC_ORIGIN", origin: currentOrigin });
      await chrome.permissions.remove({ origins: [originPattern] });
      if (!response?.ok) throw new Error();
    }
    settings = await getSettings();
    render();
  } catch {
    showError("Could not update formatting for this site.");
  }
});

void (async () => {
  settings = await getSettings();
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  try {
    currentOrigin = tab?.url ? new URL(tab.url).origin : null;
    if (!currentOrigin || !/^https?:/.test(currentOrigin)) throw new Error();
    siteName.textContent = new URL(currentOrigin).hostname;
    genericToggle.disabled = false;
  } catch {
    siteName.textContent = "Unavailable on this page";
  }
  render();
})();
