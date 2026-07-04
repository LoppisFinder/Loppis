"use client";

import type { ReactNode } from "react";
import { I18nProvider } from "@/lib/i18n/context";
import { ThemeProvider } from "@/lib/theme/context";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <I18nProvider>{children}</I18nProvider>
    </ThemeProvider>
  );
}
