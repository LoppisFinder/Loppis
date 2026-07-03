import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useLocalSearchParams } from "expo-router";
import { LoppisDetail } from "@loppis/shared";
import { ensureSession, getApiClient } from "@/lib/api";
import { formatDateLong, formatDateTime } from "@/lib/format";
import { useI18n } from "@/lib/I18nProvider";
import { useTheme } from "@/lib/ThemeProvider";

export default function DetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { locale, t, reliabilityLabel } = useI18n();
  const { c } = useTheme();
  const [detail, setDetail] = useState<LoppisDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isFavorite, setIsFavorite] = useState(false);
  const [alertMsg, setAlertMsg] = useState("");

  useEffect(() => {
    if (!id) return;
    void (async () => {
      try {
        const detailData = await (await getApiClient()).getLoppis(id);
        setDetail(detailData);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const toggleFavorite = async () => {
    if (!id) return;
    await ensureSession();
    const client = await getApiClient();
    if (isFavorite) {
      const favs = await client.getFavorites();
      const fav = favs.find((f) => f.loppis_id === id);
      if (fav) await client.removeFavorite(fav.id);
      setIsFavorite(false);
    } else {
      await client.addFavorite(id);
      setIsFavorite(true);
    }
  };

  const addAlert = async () => {
    if (!id) return;
    await ensureSession();
    await (await getApiClient()).createAlert({ loppis_id: id, before_hours: 24 });
    setAlertMsg(t("alertCreated"));
  };

  if (loading || !detail) {
    return (
      <View style={[styles.center, { backgroundColor: c.bg }]}>
        <ActivityIndicator size="large" color={c.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={[styles.container, { backgroundColor: c.surface }]}>
      <Text style={[styles.title, { color: c.text }]}>{detail.title}</Text>
      <Text style={[styles.meta, { color: c.textMuted }]}>{formatDateTime(detail.start_at)}</Text>
      {detail.address_text && (
        <Text style={[styles.meta, { color: c.textMuted }]}>{detail.address_text}</Text>
      )}
      <Text style={[styles.score, { color: c.primary }]}>
        {reliabilityLabel(detail.reliability_score, detail.status)} ({Math.round(detail.reliability_score)}/100)
      </Text>

      {detail.description && (
        <Text style={[styles.body, { color: c.text }]}>{detail.description}</Text>
      )}

      {detail.score_breakdown && (
        <View style={[styles.box, { backgroundColor: c.surfaceElevated }]}>
          <Text style={[styles.section, { color: c.text }]}>{t("whyScore")}</Text>
          <Text style={{ color: c.textMuted, fontSize: 13, marginTop: 6 }}>
            {t("scoreSource")}: {detail.score_breakdown.source_trust}{"\n"}
            {t("scoreConfirm")}: {detail.score_breakdown.confirmation_count}
          </Text>
        </View>
      )}

      <Text style={[styles.section, { color: c.text }]}>{t("sources")}</Text>
      {detail.sources.map((s) => (
        <Pressable key={s.id} onPress={() => Linking.openURL(s.source_url)}>
          <Text style={{ color: c.primary, fontSize: 14, marginBottom: 4 }}>{s.source_type}</Text>
        </Pressable>
      ))}

      {detail.history.length > 0 && (
        <>
          <Text style={[styles.section, { color: c.text }]}>{t("history")}</Text>
          {detail.history.map((h) => (
            <Text key={h.id} style={[styles.body, { color: c.text }]}>
              {formatDateLong(h.occurred_at, locale)} — {h.was_accurate ? t("happened") : t("cancelledEvent")}
            </Text>
          ))}
        </>
      )}

      <Pressable style={[styles.action, { borderColor: c.primary }]} onPress={toggleFavorite}>
        <Text style={[styles.actionText, { color: c.primary }]}>
          {isFavorite ? t("favorite") : t("addFavorite")}
        </Text>
      </Pressable>
      <Pressable style={[styles.action, { borderColor: c.primary }]} onPress={addAlert}>
        <Text style={[styles.actionText, { color: c.primary }]}>{t("createAlert")}</Text>
      </Pressable>
      <Pressable
        style={[styles.action, { borderColor: c.primary }]}
        onPress={async () => {
          const client = await getApiClient();
          Linking.openURL(client.icsUrl(detail.id));
        }}
      >
        <Text style={[styles.actionText, { color: c.primary }]}>{t("addCalendar")}</Text>
      </Pressable>
      {alertMsg ? <Text style={{ color: c.successText, marginTop: 8 }}>{alertMsg}</Text> : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  title: { fontSize: 20, fontWeight: "700" },
  meta: { fontSize: 14, marginTop: 6 },
  score: { fontSize: 15, fontWeight: "600", marginTop: 12 },
  body: { fontSize: 14, marginTop: 12, lineHeight: 20 },
  section: { fontSize: 16, fontWeight: "600", marginTop: 20, marginBottom: 8 },
  box: { marginTop: 12, padding: 12, borderRadius: 8 },
  action: {
    marginTop: 12,
    padding: 14,
    borderWidth: 1,
    borderRadius: 8,
    alignItems: "center",
  },
  actionText: { fontWeight: "600" },
});
