"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { LoppisStatus } from "@loppis/shared";
import { Locale, translations } from "./translations";

type Vars = Record<string, string | number>;

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, vars?: Vars) => string;
  reliabilityLabel: (score: number, status: LoppisStatus) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

function getNested(obj: Record<string, unknown>, path: string): string | undefined {
  const parts = path.split(".");
  let cur: unknown = obj;
  for (const part of parts) {
    if (cur && typeof cur === "object" && part in (cur as Record<string, unknown>)) {
      cur = (cur as Record<string, unknown>)[part];
    } else {
      return undefined;
    }
  }
  return typeof cur === "string" ? cur : undefined;
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("sv");

  useEffect(() => {
    const stored = localStorage.getItem("loppis_locale") as Locale | null;
    if (stored === "sv" || stored === "en") setLocaleState(stored);
  }, []);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    localStorage.setItem("loppis_locale", next);
    document.documentElement.lang = next;
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const t = useCallback(
    (key: string, vars?: Vars) => {
      const raw = getNested(translations[locale] as Record<string, unknown>, key) ?? key;
      if (!vars) return raw;
      return Object.entries(vars).reduce(
        (acc, [k, v]) => acc.replace(new RegExp(`\\{${k}\\}`, "g"), String(v)),
        raw
      );
    },
    [locale]
  );

  const reliabilityLabel = useCallback(
    (score: number, status: LoppisStatus) => {
      if (status === "cancelled") return t("reliability.cancelled");
      if (score >= 70) return t("reliability.trusted");
      if (score >= 40) return t("reliability.uncertain");
      return t("reliability.unverified");
    },
    [t]
  );

  const value = useMemo(
    () => ({ locale, setLocale, t, reliabilityLabel }),
    [locale, setLocale, t, reliabilityLabel]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
