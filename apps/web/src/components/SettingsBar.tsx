"use client";

import type { Locale } from "@/lib/i18n/translations";
import { useI18n } from "@/lib/i18n/context";
import { useTheme } from "@/lib/theme/context";

export function SettingsBar() {
  const { locale, setLocale, t } = useI18n();
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="settings-bar">
      <label className="settings-control">
        <span className="settings-label">{t("language")}</span>
        <select
          value={locale}
          onChange={(e) => setLocale(e.target.value as Locale)}
          className="settings-select"
          aria-label={t("language")}
        >
          <option value="sv">Svenska</option>
          <option value="en">English</option>
        </select>
      </label>
      <button
        type="button"
        onClick={toggleTheme}
        className="settings-theme-btn"
        aria-label={t("theme")}
        title={theme === "light" ? t("themeDark") : t("themeLight")}
      >
        {theme === "light" ? "🌙" : "☀️"}
      </button>
    </div>
  );
}
