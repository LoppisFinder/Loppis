import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";import { colors, loadStoredTheme, saveTheme, type Theme, type ThemeColors } from "@/lib/theme";

interface ThemeContextValue {
  theme: Theme;
  c: ThemeColors;
  toggleTheme: () => void;
  ready: boolean;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("light");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    loadStoredTheme().then((t) => {
      setThemeState(t);
      setReady(true);
    });
  }, []);

  const toggleTheme = () => {
    setThemeState((prev) => {
      const next = prev === "light" ? "dark" : "light";
      saveTheme(next);
      return next;
    });
  };

  const value = useMemo(
    () => ({ theme, c: colors[theme], toggleTheme, ready }),
    [theme, ready]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
