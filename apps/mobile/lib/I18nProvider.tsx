"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { LoppisStatus } from "@loppis/shared";
import {
  loadStoredLocale,
  saveLocale,
  translate,
  reliabilityLabel as relLabel,
  type Locale,
} from "@/lib/i18n";

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
  reliabilityLabel: (score: number, status: LoppisStatus) => string;
  ready: boolean;
}

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("sv");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    loadStoredLocale().then((l) => {
      setLocaleState(l);
      setReady(true);
    });
  }, []);

  const setLocale = (next: Locale) => {
    setLocaleState(next);
    saveLocale(next);
  };

  const value = useMemo(
    () => ({
      locale,
      setLocale,
      ready,
      t: (key: string, vars?: Record<string, string | number>) => translate(locale, key, vars),
      reliabilityLabel: (score: number, status: LoppisStatus) => relLabel(locale, score, status),
    }),
    [locale, ready]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
