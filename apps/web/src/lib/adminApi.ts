import { API_BASE_URL } from "@loppis/shared";

const TOKEN_KEY = "loppis_admin_token";

export type FeedSource = {
  id: string;
  name: string;
  url: string;
  kind: "calendar" | "facebook_group";
  pages: string[] | null;
  enabled: boolean;
  created_at: string;
};

export type CrawlSettings = {
  auto_enabled: boolean;
  interval_hours: number;
  auto_discover: boolean;
  include_search: boolean;
  include_social: boolean;
  data_version: string;
  last_run_at: string | null;
  last_ingested: number;
};

export type CrawlStatus = {
  running: boolean;
  message: string | null;
  last_report: {
    discovered: number;
    ingested: number;
    skipped: number;
    by_source: Record<string, number>;
    errors: string[];
  } | null;
};

function adminHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export function getAdminToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setAdminToken(token: string) {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearAdminToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}

export async function adminLogin(password: string): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/v1/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Login failed: ${res.status}`);
  }
  const data = await res.json();
  setAdminToken(data.access_token);
  return data.access_token;
}

async function adminFetch<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { ...adminHeaders(token), ...(init?.headers ?? {}) },
  });
  if (res.status === 401) {
    clearAdminToken();
    throw new Error("Session expired — log in again");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export function listSources(token: string) {
  return adminFetch<FeedSource[]>("/v1/admin/sources", token);
}

export function createSource(
  token: string,
  data: { name: string; url: string; kind: FeedSource["kind"]; pages?: string[] }
) {
  return adminFetch<FeedSource>("/v1/admin/sources", token, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function toggleSource(token: string, id: string, enabled: boolean) {
  return adminFetch<FeedSource>(`/v1/admin/sources/${id}?enabled=${enabled}`, token, {
    method: "PATCH",
  });
}

export function deleteSource(token: string, id: string) {
  return adminFetch<{ deleted: boolean }>(`/v1/admin/sources/${id}`, token, { method: "DELETE" });
}

export function getCrawlSettings(token: string) {
  return adminFetch<CrawlSettings>("/v1/admin/crawl/settings", token);
}

export function updateCrawlSettings(token: string, patch: Partial<CrawlSettings>) {
  return adminFetch<CrawlSettings>("/v1/admin/crawl/settings", token, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function getCrawlStatus(token: string) {
  return adminFetch<CrawlStatus>("/v1/admin/crawl/status", token);
}

export function runCrawl(token: string) {
  return adminFetch<{ errors: string[] }>("/v1/admin/crawl/run", token, { method: "POST" });
}
