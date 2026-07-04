"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  adminLogin,
  clearAdminToken,
  createSource,
  deleteSource,
  getAdminToken,
  getCrawlSettings,
  getCrawlStatus,
  listSources,
  runCrawl,
  syncRegistrySources,
  toggleSource,
  updateCrawlSettings,
  type CrawlSettings,
  type FeedSource,
} from "@/lib/adminApi";

export default function AdminPage() {
  const [token, setToken] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [sources, setSources] = useState<FeedSource[]>([]);
  const [settings, setSettings] = useState<CrawlSettings | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [crawlRunning, setCrawlRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [newName, setNewName] = useState("");
  const [newUrl, setNewUrl] = useState("");
  const [newKind, setNewKind] = useState<FeedSource["kind"]>("calendar");
  const [newPages, setNewPages] = useState("/");

  useEffect(() => {
    setToken(getAdminToken());
  }, []);

  const loadAll = useCallback(async (adminToken: string) => {
    setError(null);
    const [src, cfg] = await Promise.all([listSources(adminToken), getCrawlSettings(adminToken)]);
    setSources(src);
    setSettings(cfg);
  }, []);

  useEffect(() => {
    if (!token) return;
    loadAll(token).catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
  }, [token, loadAll]);

  useEffect(() => {
    if (!token || !crawlRunning) return;
    const timer = setInterval(async () => {
      try {
        const status = await getCrawlStatus(token);
        if (status.message) setStatusMsg(status.message);
        if (!status.running) {
          setCrawlRunning(false);
          if (status.last_report) {
            setStatusMsg(
              `Done — ${status.last_report.ingested} new listings (${status.last_report.discovered} found)`
            );
          }
          await loadAll(token);
        }
      } catch {
        setCrawlRunning(false);
      }
    }, 2000);
    return () => clearInterval(timer);
  }, [token, crawlRunning, loadAll]);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    try {
      const t = await adminLogin(password);
      setToken(t);
      setPassword("");
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : "Login failed");
    }
  };

  const handleLogout = () => {
    clearAdminToken();
    setToken(null);
    setSources([]);
    setSettings(null);
  };

  const handleAddSource = async (e: FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      const pages =
        newKind === "calendar"
          ? newPages
              .split(",")
              .map((p) => p.trim())
              .filter(Boolean)
          : undefined;
      await createSource(token, { name: newName, url: newUrl, kind: newKind, pages });
      setNewName("");
      setNewUrl("");
      setNewPages("/");
      await loadAll(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add source");
    }
  };

  const handleRunCrawl = async () => {
    if (!token) return;
    setCrawlRunning(true);
    setStatusMsg("Starting crawl…");
    try {
      await runCrawl(token);
    } catch (err) {
      setCrawlRunning(false);
      setError(err instanceof Error ? err.message : "Crawl failed to start");
    }
  };

  const saveSettings = async (patch: Partial<CrawlSettings>) => {
    if (!token || !settings) return;
    try {
      const updated = await updateCrawlSettings(token, patch);
      setSettings(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save settings");
    }
  };

  if (!token) {
    return (
      <div className="admin-shell">
        <div className="admin-card">
          <h1>LoppisFinder Admin</h1>
          <p className="admin-muted">Log in to manage crawl sources and schedules.</p>
          <form onSubmit={handleLogin} className="admin-form">
            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </label>
            {loginError && <div className="banner banner-error">{loginError}</div>}
            <button type="submit" className="btn-primary">
              Log in
            </button>
          </form>
          <p className="admin-muted">
            <Link href="/">← Back to map</Link>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-shell">
      <header className="admin-header">
        <div>
          <h1>LoppisFinder Admin</h1>
          <p className="admin-muted">Manage sources, run crawls, configure auto schedule.</p>
        </div>
        <div className="admin-header-actions">
          <Link href="/">Public site</Link>
          <button type="button" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </header>

      {error && <div className="banner banner-error">{error}</div>}
      {statusMsg && <div className="banner banner-success">{statusMsg}</div>}

      <section className="admin-section">
        <h2>Scheduled crawl</h2>
        {settings && (
          <div className="admin-grid">
            <label className="admin-check">
              <input
                type="checkbox"
                checked={settings.auto_enabled}
                onChange={(e) => saveSettings({ auto_enabled: e.target.checked })}
              />
              Auto crawl enabled
            </label>
            <label>
              Interval (hours)
              <input
                type="number"
                min={0.5}
                max={168}
                step={0.5}
                value={settings.interval_hours}
                onChange={(e) => saveSettings({ interval_hours: Number(e.target.value) })}
              />
            </label>
            <label className="admin-check">
              <input
                type="checkbox"
                checked={settings.auto_discover}
                onChange={(e) => saveSettings({ auto_discover: e.target.checked })}
              />
              Auto-discover new sources
            </label>
            <label className="admin-check">
              <input
                type="checkbox"
                checked={settings.include_search}
                onChange={(e) => saveSettings({ include_search: e.target.checked })}
              />
              Deep web search (slow)
            </label>
            <label className="admin-check">
              <input
                type="checkbox"
                checked={settings.include_social}
                onChange={(e) => saveSettings({ include_social: e.target.checked })}
              />
              Social crawl (Playwright)
            </label>
          </div>
        )}
        <button type="button" className="btn-primary" onClick={handleRunCrawl} disabled={crawlRunning}>
          {crawlRunning ? "Crawl running…" : "Run crawl now"}
        </button>
        {settings?.last_run_at && (
          <p className="admin-muted">
            Last run: {new Date(settings.last_run_at).toLocaleString()} — {settings.last_ingested} ingested
          </p>
        )}
      </section>

      <section className="admin-section">
        <h2>Crawl sources</h2>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={() =>
              token &&
              syncRegistrySources(token)
                .then((result) => {
                  setStatusMsg(
                    `Imported registry — ${result.added} added, ${result.updated} updated (${result.calendar_sites} sites)`
                  );
                  return loadAll(token);
                })
                .catch((err) => setError(err instanceof Error ? err.message : "Import failed"))
            }
          >
            Import from local registry file
          </button>
        </div>
        <form onSubmit={handleAddSource} className="admin-form admin-form-inline">
          <input
            placeholder="Name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            required
          />
          <input
            placeholder="URL"
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            required
          />
          <select value={newKind} onChange={(e) => setNewKind(e.target.value as FeedSource["kind"])}>
            <option value="calendar">Calendar site</option>
            <option value="facebook_group">Facebook group</option>
          </select>
          {newKind === "calendar" && (
            <input
              placeholder="Pages (comma-separated, e.g. /,/kalender.html)"
              value={newPages}
              onChange={(e) => setNewPages(e.target.value)}
            />
          )}
          <button type="submit" className="btn-primary">
            Add source
          </button>
        </form>

        <table className="admin-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>URL</th>
              <th>Kind</th>
              <th>Enabled</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => (
              <tr key={source.id}>
                <td>{source.name}</td>
                <td>
                  <a href={source.url} target="_blank" rel="noreferrer">
                    {source.url}
                  </a>
                </td>
                <td>{source.kind}</td>
                <td>
                  <input
                    type="checkbox"
                    checked={source.enabled}
                    onChange={(e) =>
                      toggleSource(token, source.id, e.target.checked)
                        .then(() => loadAll(token))
                        .catch((err) => setError(err.message))
                    }
                  />
                </td>
                <td>
                  <button
                    type="button"
                    onClick={() =>
                      deleteSource(token, source.id)
                        .then(() => loadAll(token))
                        .catch((err) => setError(err.message))
                    }
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
