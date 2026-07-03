import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import MapView, { Circle, Marker, PROVIDER_GOOGLE } from "react-native-maps";
import * as Location from "expo-location";
import { router } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import { DEFAULT_RADIUS_KM, LoppisSummary, STOCKHOLM } from "@loppis/shared";
import { FilterBar } from "@/components/FilterBar";
import { MonthCalendar } from "@/components/MonthCalendar";
import { SettingsBar } from "@/components/SettingsBar";
import { currentYearRange, endOfDay, startOfDay, type DateRange } from "@/lib/dates";
import { formatDateLong } from "@/lib/format";
import { getApiClient } from "@/lib/api";
import { runCrawlAndWait } from "@/lib/crawl";
import { useI18n } from "@/lib/I18nProvider";
import { useTheme } from "@/lib/ThemeProvider";

export default function MapScreen() {
  const { t, reliabilityLabel, ready: i18nReady, locale } = useI18n();
  const { c, ready: themeReady } = useTheme();
  const [loppis, setLoppis] = useState<LoppisSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [center, setCenter] = useState(STOCKHOLM);
  const [radiusKm, setRadiusKm] = useState(DEFAULT_RADIUS_KM);
  const [dateRange, setDateRange] = useState<DateRange>(currentYearRange);
  const [minScore, setMinScore] = useState(0);
  const [crawlMsg, setCrawlMsg] = useState<string | null>(null);
  const [crawling, setCrawling] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const data = await (await getApiClient()).listLoppis({
        lat: center.lat,
        lng: center.lng,
        radius_km: radiusKm,
        from: startOfDay(dateRange.from).toISOString(),
        to: endOfDay(dateRange.to).toISOString(),
        min_score: minScore,
      });
      setLoppis(data);
    } catch (e) {
      console.error(e);
      setLoppis([]);
      setFetchError(t("fetchError"));
    } finally {
      setLoading(false);
    }
  }, [center, radiusKm, dateRange, minScore, t]);

  useEffect(() => {
    if (i18nReady && themeReady) fetchData();
  }, [fetchData, i18nReady, themeReady]);

  const useMyLocation = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== "granted") return;
    const loc = await Location.getCurrentPositionAsync({});
    setCenter({ lat: loc.coords.latitude, lng: loc.coords.longitude });
  };

  const runCrawl = async () => {
    setCrawling(true);
    setCrawlMsg(t("crawlStart"));
    try {
      const report = await runCrawlAndWait();
      setCrawlMsg(t("crawlDone", { ingested: report.ingested, discovered: report.discovered }));
      fetchData();
    } catch (e) {
      setCrawlMsg(e instanceof Error ? e.message : t("crawlFail"));
    } finally {
      setCrawling(false);
    }
  };

  const delta = Math.max(0.05, radiusKm / 111);

  if (!i18nReady || !themeReady) {
    return (
      <View style={[styles.center, { backgroundColor: c.bg }]}>
        <ActivityIndicator color={c.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: c.bg }]} edges={["bottom"]}>
      <View style={[styles.header, { backgroundColor: c.surface, borderColor: c.border }]}>
        <SettingsBar />
        <Pressable
          style={[styles.crawlBtn, { backgroundColor: crawling ? c.primarySoft : c.primary, borderColor: c.primary }]}
          onPress={runCrawl}
          disabled={crawling}
        >
          <Text style={[styles.crawlText, { color: crawling ? c.text : c.primaryText }]}>
            {crawling ? t("fetching") : t("fetchReal")}
          </Text>
        </Pressable>
        <Text style={[styles.count, { color: c.textMuted }]}>{t("countLoppis", { count: loppis.length })}</Text>
        <Pressable onPress={() => router.push("/favorites")}>
          <Text style={[styles.favLink, { color: c.primary }]}>{t("favorites")}</Text>
        </Pressable>
      </View>

      {crawlMsg && (
        <Text style={[styles.banner, { backgroundColor: c.successBg, color: c.successText }]}>{crawlMsg}</Text>
      )}
      {fetchError && (
        <Text style={[styles.banner, { backgroundColor: c.errorBg, color: c.errorText }]}>{fetchError}</Text>
      )}

      <FilterBar
        radiusKm={radiusKm}
        dateRange={dateRange}
        minScore={minScore}
        onRadiusChange={setRadiusKm}
        onMinScoreChange={setMinScore}
        onUseLocation={useMyLocation}
      />

      <MapView
        style={styles.map}
        provider={PROVIDER_GOOGLE}
        region={{
          latitude: center.lat,
          longitude: center.lng,
          latitudeDelta: delta,
          longitudeDelta: delta,
        }}
        onPress={(e) => setCenter({ lat: e.nativeEvent.coordinate.latitude, lng: e.nativeEvent.coordinate.longitude })}
      >
        <Circle
          center={{ latitude: center.lat, longitude: center.lng }}
          radius={radiusKm * 1000}
          strokeColor="rgba(37,99,235,0.6)"
          fillColor="rgba(37,99,235,0.12)"
        />
        <Marker
          coordinate={{ latitude: center.lat, longitude: center.lng }}
          pinColor="#dc2626"
          draggable
          onDragEnd={(e) =>
            setCenter({
              lat: e.nativeEvent.coordinate.latitude,
              lng: e.nativeEvent.coordinate.longitude,
            })
          }
        />
        {loppis.map((item) => (
          <Marker
            key={item.id}
            coordinate={{ latitude: item.lat, longitude: item.lng }}
            title={item.title}
            description={formatDateLong(item.start_at, locale)}
            onCalloutPress={() => router.push({ pathname: "/detail", params: { id: item.id } })}
          />
        ))}
      </MapView>

      <View style={[styles.bottom, { backgroundColor: c.surface, borderColor: c.border }]}>
        <MonthCalendar range={dateRange} onRangeChange={setDateRange} loppis={loppis} />
        {loading ? (
          <ActivityIndicator style={{ padding: 16 }} color={c.primary} />
        ) : (
          <FlatList
            style={styles.list}
            data={loppis}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <Pressable
                style={[styles.listItem, { borderColor: c.border }]}
                onPress={() => router.push({ pathname: "/detail", params: { id: item.id } })}
              >
                <Text style={[styles.title, { color: c.text }]}>{item.title}</Text>
                <Text style={[styles.meta, { color: c.textMuted }]}>
                  {formatDateLong(item.start_at, locale)}
                  {item.municipality ? ` · ${item.municipality}` : ""}
                </Text>
                <Text style={[styles.score, { color: c.primary }]}>
                  {reliabilityLabel(item.reliability_score, item.status)}
                </Text>
              </Pressable>
            )}
            ListEmptyComponent={<Text style={[styles.empty, { color: c.textMuted }]}>{t("emptyList")}</Text>}
          />
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderBottomWidth: 1,
    flexWrap: "wrap",
  },
  crawlBtn: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 6, borderWidth: 1 },
  crawlText: { fontSize: 12, fontWeight: "600" },
  count: { fontSize: 12 },
  favLink: { fontSize: 13, fontWeight: "600" },
  banner: { padding: 8, fontSize: 12 },
  map: { flex: 1, minHeight: 220 },
  bottom: { maxHeight: "42%", borderTopWidth: 1 },
  list: { maxHeight: 160 },
  listItem: { padding: 12, borderBottomWidth: 1 },
  title: { fontWeight: "600", fontSize: 14 },
  meta: { fontSize: 12, marginTop: 2 },
  score: { fontSize: 11, marginTop: 4, fontWeight: "600" },
  empty: { padding: 16, textAlign: "center" },
});
