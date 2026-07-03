"use client";

import { FilterPanel } from "@/components/FilterPanel";
import { useI18n } from "@/lib/i18n/context";
import { formatRangeLabel, type DateRange } from "@/lib/dates";

interface Props {
  radiusKm: number;
  dateRange: DateRange;
  minScore: number;
  onRadiusChange: (v: number) => void;
  onMinScoreChange: (v: number) => void;
  onUseLocation: () => void;
}

export function FilterPanel({
  radiusKm,
  dateRange,
  minScore,
  onRadiusChange,
  onMinScoreChange,
  onUseLocation,
}: Props) {
  const { locale, t } = useI18n();

  return (
    <div className="filter-panel">
      <span style={{ fontSize: 14, color: "var(--color-text-muted)" }}>
        {t("period")}: <strong style={{ color: "var(--color-text)" }}>{formatRangeLabel(locale, dateRange)}</strong>
      </span>

      <label className="filter-label">
        {t("radius")}: {t("radiusKm", { km: radiusKm })}
        <input
          type="range"
          min={5}
          max={200}
          value={radiusKm}
          onChange={(e) => onRadiusChange(Number(e.target.value))}
        />
      </label>

      <label className="filter-label">
        {t("minReliability")}: {minScore}
        <input
          type="range"
          min={0}
          max={100}
          step={10}
          value={minScore}
          onChange={(e) => onMinScoreChange(Number(e.target.value))}
        />
      </label>

      <button type="button" onClick={onUseLocation} className="btn-secondary">
        {t("myLocation")}
      </button>

      <span className="filter-hint">{t("mapHint")}</span>
    </div>
  );
}
