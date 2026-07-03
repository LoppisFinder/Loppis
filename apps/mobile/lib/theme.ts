import * as SecureStore from "expo-secure-store";

export type Theme = "light" | "dark";

export const colors = {
  light: {
    bg: "#f5f5f5",
    surface: "#ffffff",
    surfaceMuted: "#fafafa",
    surfaceElevated: "#f9fafb",
    border: "#e5e5e5",
    text: "#1a1a1a",
    textMuted: "#666666",
    textSubtle: "#888888",
    primary: "#2563eb",
    primarySoft: "#dbeafe",
    primaryText: "#ffffff",
    successBg: "#ecfdf5",
    successText: "#065f46",
    errorBg: "#fef2f2",
    errorText: "#991b1b",
    currentMonth: "#f59e0b",
    currentMonthSoft: "#fffbeb",
    scoreHigh: "#dcfce7",
    scoreMid: "#fef9c3",
    scoreLow: "#fee2e2",
  },
  dark: {
    bg: "#0f172a",
    surface: "#1e293b",
    surfaceMuted: "#172033",
    surfaceElevated: "#334155",
    border: "#334155",
    text: "#f1f5f9",
    textMuted: "#94a3b8",
    textSubtle: "#64748b",
    primary: "#3b82f6",
    primarySoft: "#1e3a5f",
    primaryText: "#ffffff",
    successBg: "#064e3b",
    successText: "#a7f3d0",
    errorBg: "#450a0a",
    errorText: "#fecaca",
    currentMonth: "#fbbf24",
    currentMonthSoft: "#422006",
    scoreHigh: "#14532d",
    scoreMid: "#422006",
    scoreLow: "#450a0a",
  },
} as const;

export type ThemeColors = (typeof colors)["light"];

const THEME_KEY = "loppis_theme";

export async function loadStoredTheme(): Promise<Theme> {
  const stored = await SecureStore.getItemAsync(THEME_KEY);
  return stored === "dark" ? "dark" : "light";
}

export async function saveTheme(theme: Theme): Promise<void> {
  await SecureStore.setItemAsync(THEME_KEY, theme);
}
