import { Pressable, StyleSheet, Text, View } from "react-native";
import { useI18n } from "@/lib/I18nProvider";
import { useTheme } from "@/lib/ThemeProvider";
import type { Locale } from "@/lib/i18n";

export function SettingsBar() {
  const { locale, setLocale, t } = useI18n();
  const { c, toggleTheme, theme } = useTheme();

  return (
    <View style={styles.row}>
      <Pressable
        style={[styles.chip, { borderColor: c.border, backgroundColor: c.surface }]}
        onPress={() => setLocale(locale === "sv" ? "en" : ("sv" as Locale))}
      >
        <Text style={[styles.chipText, { color: c.textMuted }]}>
          {locale === "sv" ? "EN" : "SV"}
        </Text>
      </Pressable>
      <Pressable
        style={[styles.chip, { borderColor: c.border, backgroundColor: c.surface }]}
        onPress={toggleTheme}
        accessibilityLabel={t("theme")}
      >
        <Text style={styles.chipText}>{theme === "light" ? "🌙" : "☀️"}</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: 6 },
  chip: {
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  chipText: { fontSize: 13, fontWeight: "600" },
});
