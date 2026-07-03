"use client";

import { useEffect, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import {
  API_BASE_URL,
  DEFAULT_RADIUS_KM,
  LoppisApiClient,
  LoppisSummary,
  STOCKHOLM,
} from "@loppis/shared";
import { FilterPanel } from "@/components/FilterPanel";
import { LoppisDetailPanel } from "@/components/LoppisDetailPanel";
import { LoppisList } from "@/components/LoppisList";
import { MonthCalendar } from "@/components/MonthCalendar";
import { SessionBanner } from "@/components/SessionBanner";
import { SettingsBar } from "@/components/SettingsBar";
import { currentYearRange, endOfDay, startOfDay, type DateRange } from "@/lib/dates";
import { useI18n } from "@/lib/i18n/context";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

export default function HomePage() {
  const { t } = useI18n();
  const [client] = useState(() => new LoppisApiClient(API_BASE_URL));
  const [token, setToken] = useState<string | null>(null);
  const [loppis, setLoppis] = useState<LoppisSummary[]>([]);
  const [selected, setSelected] = useState<LoppisSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [center, setCenter] = useState(STOCKHOLM);
  const [radiusKm, setRadiusKm] = useState(DEFAULT_RADIUS_KM);
  const [dateRange, setDateRange] = useState<DateRange>(currentYearRange);
  const [minScore, setMinScore] = useState(0);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [panToCenter, setPanToCenter] = useState(false);
  const [crawlMsg, setCrawlMsg] = useState<string | null>(null);
  const [crawling, setCrawling] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("loppis_token");
    if (stored) {
      client.setToken(stored);
      setToken(stored);
    }
  }, [client]);

  const fetchLoppis = useCallback(async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const data = await client.listLoppis({
        lat: center.lat,
        lng: center.lng,
        radius_km: radiusKm,
        from: startOfDay(dateRange.from).toISOString(),
        to: endOfDay(dateRange.to).toISOString(),
        min_score: minScore,
      });
      setLoppis(data);
    } catch (e) {
      console.error(e);
      setLoppis([]);
      setFetchError(e instanceof Error ? e.message : t("fetchError"));
    } finally {
      setLoading(false);
    }
  }, [client, center, radiusKm, minScore, dateRange, t]);

  useEffect(() => {
    fetchLoppis();
  }, [fetchLoppis]);

  useEffect(() => {
    if (!token) return;
    client
      .getFavorites()
      .then((favs) => {
        setFavorites(new Set(favs.map((f) => f.loppis_id)));
      })
      .catch(() => {});
  }, [client, token]);

  const ensureSession = async () => {
    if (token) return token;
    const session = await client.createAnonymousSession();
    localStorage.setItem("loppis_token", session.access_token);
    client.setToken(session.access_token);
    setToken(session.access_token);
    return session.access_token;
  };

  const toggleFavorite = async (loppisId: string) => {
    await ensureSession();
    if (favorites.has(loppisId)) {
      const favs = await client.getFavorites();
      const fav = favs.find((f) => f.loppis_id === loppisId);
      if (fav) {
        await client.removeFavorite(fav.id);
        setFavorites((prev) => {
          const next = new Set(prev);
          next.delete(loppisId);
          return next;
        });
      }
    } else {
      await client.addFavorite(loppisId);
      setFavorites((prev) => new Set(prev).add(loppisId));
    }
  };

  const useMyLocation = () => {
    navigator.geolocation?.getCurrentPosition((pos) => {
      setCenter({ lat: pos.coords.latitude, lng: pos.coords.longitude });
      setPanToCenter(true);
    });
  };

  const handleCenterChange = useCallback((lat: number, lng: number) => {
    setCenter({ lat, lng });
    setPanToCenter(false);
    setSelected(null);
  }, []);

  const runCrawl = async () => {
    setCrawling(true);
    setCrawlMsg(t("crawlStart"));
    try {
      const start = await fetch(`${API_BASE_URL}/v1/crawl/run`, { method: "POST" });
      if (!start.ok) throw new Error(`Crawl failed: ${start.status}`);

      for (let i = 0; i < 120; i++) {
        const statusRes = await fetch(`${API_BASE_URL}/v1/crawl/status`);
        if (statusRes.ok) {
          const status = await statusRes.json();
          if (status.message) setCrawlMsg(status.message);
          if (status.running) {
            await new Promise((r) => setTimeout(r, 2000));
            continue;
          }
          if (status.last_report) {
            const data = status.last_report;
            setCrawlMsg(
              t("crawlDone", { ingested: data.ingested, discovered: data.discovered })
            );
            await fetch(`${API_BASE_URL}/v1/crawl/seed-examples`, { method: "DELETE" });
            fetchLoppis();
            return;
          }
          if (status.message?.startsWith("Fel:")) {
            throw new Error(status.message);
          }
        }
        await new Promise((r) => setTimeout(r, 2000));
      }
      setCrawlMsg(t("crawlSlow"));
    } catch (e) {
      setCrawlMsg(e instanceof Error ? e.message : t("crawlFail"));
    } finally {
      setCrawling(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1 className="app-header-title">{t("appTitle")}</h1>
        <div className="app-header-actions">
          <SettingsBar />
          <button type="button" onClick={runCrawl} disabled={crawling} className="btn-primary">
            {crawling ? t("fetching") : t("fetchReal")}
          </button>
          <span style={{ fontSize: "0.875rem", color: "var(--color-text-muted)" }}>
            {t("countLoppis", { count: loppis.length })}
          </span>
        </div>
      </header>

      <SessionBanner hasSession={!!token} onCreateSession={ensureSession} />

      {crawlMsg && <div className="banner banner-success">{crawlMsg}</div>}
      {fetchError && <div className="banner banner-error">{fetchError}</div>}

      <FilterPanel
        radiusKm={radiusKm}
        dateRange={dateRange}
        minScore={minScore}
        onRadiusChange={setRadiusKm}
        onMinScoreChange={setMinScore}
        onUseLocation={useMyLocation}
      />

      <div style={{ flex: 1, display: "flex", minHeight: 0 }}>
        <div style={{ flex: 1, position: "relative" }}>
          <MapView
            center={center}
            loppis={loppis}
            selectedId={selected?.id}
            onSelect={setSelected}
            radiusKm={radiusKm}
            onCenterChange={handleCenterChange}
            panToCenter={panToCenter}
            onPanComplete={() => setPanToCenter(false)}
          />
        </div>
        <aside className="app-sidebar">
          {!selected && (
            <MonthCalendar range={dateRange} onRangeChange={setDateRange} loppis={loppis} />
          )}
          {selected ? (
            <LoppisDetailPanel
              loppis={selected}
              client={client}
              isFavorite={favorites.has(selected.id)}
              onToggleFavorite={() => toggleFavorite(selected.id)}
              onClose={() => setSelected(null)}
              onEnsureSession={ensureSession}
            />
          ) : (
            <LoppisList loppis={loppis} loading={loading} onSelect={setSelected} />
          )}
        </aside>
      </div>
    </div>
  );
}
