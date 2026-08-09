import { getSettings, saveSettings } from "./settings";

function scriptId(origin: string): string {
  return `clean-paste-generic-${Array.from(origin).reduce((hash, character) => ((hash * 31 + character.charCodeAt(0)) >>> 0), 7).toString(36)}`;
}

async function registerGenericOrigin(origin: string): Promise<void> {
  const id = scriptId(origin);
  await chrome.scripting.unregisterContentScripts({ ids: [id] }).catch(() => undefined);
  await chrome.scripting.registerContentScripts([{ id, matches: [`${origin}/*`], js: ["content-generic.js"], runAt: "document_start", persistAcrossSessions: true }]);
}

async function removeGenericOrigin(origin: string): Promise<void> {
  await chrome.scripting.unregisterContentScripts({ ids: [scriptId(origin)] }).catch(() => undefined);
}

chrome.runtime.onInstalled.addListener(() => {
  void getSettings().then(saveSettings);
});

chrome.runtime.onStartup.addListener(() => {
  void getSettings().then(async (settings) => {
    await Promise.all(settings.genericOrigins.map(registerGenericOrigin));
  });
});

chrome.runtime.onMessage.addListener((message: { type?: string; origin?: string }, _sender, sendResponse) => {
  if (!message.origin || !["ENABLE_GENERIC_ORIGIN", "DISABLE_GENERIC_ORIGIN"].includes(message.type ?? "")) return;
  void (async () => {
    try {
      const settings = await getSettings();
      if (message.type === "ENABLE_GENERIC_ORIGIN") {
        if (!settings.genericOrigins.includes(message.origin!)) settings.genericOrigins.push(message.origin!);
        await registerGenericOrigin(message.origin!);
      } else {
        settings.genericOrigins = settings.genericOrigins.filter((origin) => origin !== message.origin);
        await removeGenericOrigin(message.origin!);
      }
      await saveSettings(settings);
      sendResponse({ ok: true });
    } catch {
      sendResponse({ ok: false });
    }
  })();
  return true;
});
