import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { I18nProvider } from "@/lib/I18nProvider";
import { ThemeProvider } from "@/lib/ThemeProvider";
import { useTheme } from "@/lib/ThemeProvider";
import { useI18n } from "@/lib/I18nProvider";

function RootStack() {
  const { theme } = useTheme();
  const { t } = useI18n();

  return (
    <>
      <StatusBar style={theme === "dark" ? "light" : "dark"} />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: theme === "dark" ? "#1e293b" : "#fff" },
          headerTintColor: theme === "dark" ? "#f1f5f9" : "#1a1a1a",
        }}
      >
        <Stack.Screen name="index" options={{ title: t("appTitle") }} />
        <Stack.Screen name="detail" options={{ title: "LoppisFinder" }} />
        <Stack.Screen name="favorites" options={{ title: t("favorites") }} />
      </Stack>
    </>
  );
}

export default function RootLayout() {
  return (
    <ThemeProvider>
      <I18nProvider>
        <RootStack />
      </I18nProvider>
    </ThemeProvider>
  );
}
