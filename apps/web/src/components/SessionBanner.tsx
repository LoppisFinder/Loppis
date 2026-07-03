"use client";

import { useI18n } from "@/lib/i18n/context";

interface Props {
  hasSession: boolean;
  onCreateSession: () => Promise<string>;
}

export function SessionBanner({ hasSession, onCreateSession }: Props) {
  const { t } = useI18n();

  if (hasSession) {
    return <div className="banner banner-success">{t("sessionActive")}</div>;
  }

  return (
    <div
      className="banner banner-info"
      style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}
    >
      <span>{t("sessionPrompt")}</span>
      <button type="button" onClick={onCreateSession} className="btn-primary">
        {t("startSession")}
      </button>
    </div>
  );
}
