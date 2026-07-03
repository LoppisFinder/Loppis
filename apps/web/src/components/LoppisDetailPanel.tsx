"use client";

import { useEffect, useState } from "react";
import { LoppisApiClient, LoppisDetail, LoppisSummary } from "@loppis/shared";
import { useI18n } from "@/lib/i18n/context";
import { formatDateLong, formatDateTime } from "@/lib/format";

interface Props {
  loppis: LoppisSummary;
  client: LoppisApiClient;
  isFavorite: boolean;
  onToggleFavorite: () => void;
  onClose: () => void;
  onEnsureSession: () => Promise<string>;
}

export function LoppisDetailPanel({
  loppis,
  client,
  isFavorite,
  onToggleFavorite,
  onClose,
  onEnsureSession,
}: Props) {
  const { locale, t, reliabilityLabel } = useI18n();
  const [detail, setDetail] = useState<LoppisDetail | null>(null);
  const [alertHours, setAlertHours] = useState(24);
  const [alertMsg, setAlertMsg] = useState("");

  useEffect(() => {
    client.getLoppis(loppis.id).then(setDetail).catch(console.error);
  }, [client, loppis.id]);

  const setAlert = async () => {
    await onEnsureSession();
    await client.createAlert({ loppis_id: loppis.id, before_hours: alertHours });
    setAlertMsg(t("alertCreated"));
  };

  return (
    <div className="detail-panel">
      <button type="button" onClick={onClose} className="btn-secondary" style={{ marginBottom: 12 }}>
        {t("back")}
      </button>
      <h2 style={{ fontSize: "1.125rem", marginBottom: 8 }}>{loppis.title}</h2>
      <p className="detail-muted">
        {formatDateTime(loppis.start_at)}
        {loppis.address_text ? ` · ${loppis.address_text}` : ""}
      </p>
      <p style={{ marginTop: 8 }}>
        <strong>{reliabilityLabel(loppis.reliability_score, loppis.status)}</strong> —{" "}
        {Math.round(loppis.reliability_score)}/100
      </p>

      {detail?.description && <p style={{ marginTop: 12, fontSize: 14 }}>{detail.description}</p>}

      {detail?.score_breakdown && (
        <div className="detail-score-box">
          <strong>{t("whyScore")}</strong>
          <ul style={{ marginTop: 8, paddingLeft: 20 }}>
            <li>
              {t("scoreSource")}: {detail.score_breakdown.source_trust}
            </li>
            <li>
              {t("scoreConfirm")}: {detail.score_breakdown.confirmation_count}
            </li>
            <li>
              {t("scoreFeedback")}: {detail.score_breakdown.feedback_sentiment}
            </li>
            <li>
              {t("scoreHistory")}: {detail.score_breakdown.historical_accuracy}
            </li>
            <li>
              {t("scoreFresh")}: {detail.score_breakdown.freshness}
            </li>
          </ul>
        </div>
      )}

      {detail?.sources && detail.sources.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <strong>{t("sources")}</strong>
          <ul style={{ marginTop: 8, paddingLeft: 20, fontSize: 14 }}>
            {detail.sources.map((s) => (
              <li key={s.id}>
                <a href={s.source_url} target="_blank" rel="noopener noreferrer">
                  {s.source_type}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {detail?.history && detail.history.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <strong>{t("history")}</strong>
          <ul style={{ marginTop: 8, paddingLeft: 20, fontSize: 14 }}>
            {detail.history.map((h) => (
              <li key={h.id}>
                {formatDateLong(h.occurred_at, locale)} —{" "}
                {h.was_accurate ? t("happened") : t("cancelledEvent")}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ marginTop: 20, display: "flex", flexDirection: "column", gap: 8 }}>
        <button type="button" onClick={onToggleFavorite} className="action-btn">
          {isFavorite ? t("favorite") : t("addFavorite")}
        </button>
        <a
          href={client.icsUrl(loppis.id)}
          download
          className="action-btn"
          style={{ textAlign: "center", textDecoration: "none" }}
        >
          {t("downloadIcs")}
        </a>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <select
            value={alertHours}
            onChange={(e) => setAlertHours(Number(e.target.value))}
            className="settings-select"
          >
            <option value={24}>{t("alertBefore24")}</option>
            <option value={2}>{t("alertBefore2")}</option>
          </select>
          <button type="button" onClick={setAlert} className="action-btn">
            {t("createAlert")}
          </button>
        </div>
        {alertMsg && (
          <span style={{ fontSize: 13, color: "var(--color-success-text)" }}>{alertMsg}</span>
        )}
      </div>
    </div>
  );
}
