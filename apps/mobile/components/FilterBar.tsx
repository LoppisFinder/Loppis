import { Pressable, StyleSheet, Text, View } from "react-native";
import { useI18n } from "@/lib/I18nProvider";
import { useTheme } from "@/lib/ThemeProvider";
import { formatRangeLabel, type DateRange } from "@/lib/dates";

interface Props {
  radiusKm: number;
  dateRange: DateRange;
  minScore: number;
  onRadiusChange: (v: number) => void;
  onMinScoreChange: (v: number) => void;
  onUseLocation: () => void;
}

export function FilterBar({
  radiusKm,
  dateRange,
  minScore,
  onRadiusChange,
  onMinScoreChange,
  onUseLocation,
}: Props) {
  const { locale, t } = useI18n();
  const { c } = useTheme();

  return (
    <View style={[styles.wrap, { backgroundColor: c.surface, borderColor: c.border }]}>
      <Text style={[styles.period, { color: c.textMuted }]}>
        {t("period")}: <Text style={{ color: c.text, fontWeight: "600" }}>{formatRangeLabel(locale, dateRange)}</Text>
      </Text>
      <View style={styles.row}>
        <Pressable style={[styles.btn, { borderColor: c.border, backgroundColor: c.surfaceMuted }]} onPress={onUseLocation}>
          <Text style={[styles.btnText, { color: c.primary }]}>{t("myLocation")}</Text>
        </Pressable>
        <Pressable
          style={[styles.btn, { borderColor: c.border, backgroundColor: c.surfaceMuted }]}
          onPress={() => onRadiusChange(Math.min(200, radiusKm + 25))}
        >
          <Text style={[styles.btnText, { color: c.primary }]}>{t("radiusKm", { km: radiusKm })}</Text>
        </Pressable>
        <Pressable
          style={[styles.btn, { borderColor: c.border, backgroundColor: c.surfaceMuted }]}
          onPress={() => onMinScoreChange(minScore >= 100 ? 0 : minScore + 20)}
        >
          <Text style={[styles.btnText, { color: c.primary }]}>
            {t("minReliability")}: {minScore}
          </Text>
        </Pressable>
      </View>
      <Text style={[styles.hint, { color: c.textSubtle }]}>{t("mapHint")}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { padding: 10, borderBottomWidth: 1, gap: 8 },
  period: { fontSize: 13 },
  row: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  btn: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8, borderWidth: 1 },
  btnText: { fontSize: 12, fontWeight: "600" },
  hint: { fontSize: 11 },
});
