"use client";

import { useI18n } from "@/lib/i18n/context";

type Props = {
  onRefresh: () => void;
};

export function NewLoppisBanner({ onRefresh }: Props) {
  const { t } = useI18n();

  return (
    <div className="banner banner-info new-loppis-banner">
      <span>{t("newLoppisAvailable")}</span>
      <button type="button" className="btn-primary" onClick={onRefresh}>
        {t("refreshPage")}
      </button>
    </div>
  );
}
