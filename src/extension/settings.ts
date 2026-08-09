import { PROVIDER_IDS } from "./providers";
import type { CleanPasteSettings, ProviderId } from "./types";

export const DEFAULT_SETTINGS: CleanPasteSettings = {
  enabled: true,
  providers: Object.fromEntries(PROVIDER_IDS.map((id) => [id, true])) as Record<ProviderId, boolean>,
  genericOrigins: []
};

export function mergeSettings(value: Partial<CleanPasteSettings> | undefined): CleanPasteSettings {
  return {
    enabled: value?.enabled ?? DEFAULT_SETTINGS.enabled,
    providers: { ...DEFAULT_SETTINGS.providers, ...(value?.providers ?? {}) },
    genericOrigins: value?.genericOrigins ?? []
  };
}

export async function getSettings(): Promise<CleanPasteSettings> {
  const { settings } = await chrome.storage.local.get("settings");
  return mergeSettings(settings as Partial<CleanPasteSettings> | undefined);
}

export async function saveSettings(settings: CleanPasteSettings): Promise<void> {
  await chrome.storage.local.set({ settings });
}
