import Constants from "expo-constants";
import * as SecureStore from "expo-secure-store";
import { API_BASE_URL } from "@loppis/shared";

const API_URL_KEY = "loppis_api_url";

function normalizeBaseUrl(url: string): string {
  return url.trim().replace(/\/$/, "");
}

export function getDefaultApiBaseUrl(): string {
  const fromExtra = Constants.expoConfig?.extra?.apiUrl;
  if (typeof fromExtra === "string" && fromExtra.trim()) {
    return normalizeBaseUrl(fromExtra);
  }
  return normalizeBaseUrl(API_BASE_URL);
}

export async function resolveApiBaseUrl(): Promise<string> {
  const override = await SecureStore.getItemAsync(API_URL_KEY);
  if (override?.trim()) {
    return normalizeBaseUrl(override);
  }
  return getDefaultApiBaseUrl();
}

export async function setApiBaseUrlOverride(url: string | null): Promise<void> {
  if (!url?.trim()) {
    await SecureStore.deleteItemAsync(API_URL_KEY);
    return;
  }
  await SecureStore.setItemAsync(API_URL_KEY, normalizeBaseUrl(url));
}
