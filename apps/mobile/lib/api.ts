import * as SecureStore from "expo-secure-store";
import {
  DEFAULT_RADIUS_KM,
  LoppisApiClient,
  LoppisSummary,
  STOCKHOLM,
} from "@loppis/shared";
import { resolveApiBaseUrl } from "@/lib/config";

const TOKEN_KEY = "loppis_token";

let clientInstance: LoppisApiClient | null = null;
let cachedBaseUrl: string | null = null;

export function resetApiClient(): void {
  clientInstance = null;
  cachedBaseUrl = null;
}

export async function getApiClient(): Promise<LoppisApiClient> {
  const baseUrl = await resolveApiBaseUrl();
  if (!clientInstance || cachedBaseUrl !== baseUrl) {
    clientInstance = new LoppisApiClient(baseUrl);
    cachedBaseUrl = baseUrl;
    const existing = await getStoredToken();
    if (existing) {
      clientInstance.setToken(existing);
    }
  }
  return clientInstance;
}

export async function getStoredToken(): Promise<string | null> {
  return SecureStore.getItemAsync(TOKEN_KEY);
}

export async function ensureSession(): Promise<string> {
  const client = await getApiClient();
  const existing = await getStoredToken();
  if (existing) {
    client.setToken(existing);
    return existing;
  }
  const session = await client.createAnonymousSession();
  await SecureStore.setItemAsync(TOKEN_KEY, session.access_token);
  client.setToken(session.access_token);
  return session.access_token;
}

export { DEFAULT_RADIUS_KM, STOCKHOLM };
export type { LoppisSummary };
