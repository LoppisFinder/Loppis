"use client";

import { LoppisSummary } from "@loppis/shared";
import { useI18n } from "@/lib/i18n/context";
import { formatDateLong } from "@/lib/format";

interface Props {
  loppis: LoppisSummary[];
  loading: boolean;
  onSelect: (l: LoppisSummary) => void;
}

export function LoppisList({ loppis, loading, onSelect }: Props) {
  const { locale, t, reliabilityLabel } = useI18n();

  if (loading) {
    return <p className="list-empty">{t("loadingList")}</p>;
  }
  if (loppis.length === 0) {
    return <p className="list-empty">{t("emptyList")}</p>;
  }

  return (
    <ul style={{ listStyle: "none" }}>
      {loppis.map((item) => (
        <li key={item.id} onClick={() => onSelect(item)} className="list-item">
          <div style={{ fontWeight: 600 }}>{item.title}</div>
          <div className="detail-muted" style={{ marginTop: 4 }}>
            {formatDateLong(item.start_at, locale)}
            {item.municipality ? ` · ${item.municipality}` : ""}
          </div>
          <div style={{ fontSize: 12, marginTop: 4 }}>
            <span
              style={{
                background:
                  item.reliability_score >= 70
                    ? "var(--color-score-high)"
                    : item.reliability_score >= 40
                      ? "var(--color-score-mid)"
                      : "var(--color-score-low)",
                padding: "2px 8px",
                borderRadius: 999,
              }}
            >
              {reliabilityLabel(item.reliability_score, item.status)} (
              {Math.round(item.reliability_score)})
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}
