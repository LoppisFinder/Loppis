import { useEffect, useState } from "react";
import { FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { router } from "expo-router";
import { Favorite } from "@loppis/shared";
import { ensureSession, getApiClient } from "@/lib/api";
import { useI18n } from "@/lib/I18nProvider";
import { useTheme } from "@/lib/ThemeProvider";

export default function FavoritesScreen() {
  const { t } = useI18n();
  const { c } = useTheme();
  const [favorites, setFavorites] = useState<Favorite[]>([]);

  useEffect(() => {
    void (async () => {
      await ensureSession();
      try {
        const favs = await (await getApiClient()).getFavorites();
        setFavorites(favs);
      } catch (e) {
        console.error(e);
      }
    })();
  }, []);

  return (
    <View style={[styles.container, { backgroundColor: c.surface }]}>
      <Text style={[styles.note, { backgroundColor: c.primarySoft, color: c.text }]}>{t("favoritesNote")}</Text>
      <FlatList
        data={favorites}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <Pressable
            style={[styles.item, { borderColor: c.border }]}
            onPress={() => router.push({ pathname: "/detail", params: { id: item.loppis_id } })}
          >
            <Text style={[styles.title, { color: c.text }]}>{item.loppis?.title ?? item.loppis_id}</Text>
            <Text style={[styles.date, { color: c.textMuted }]}>
              {new Date(item.created_at).toLocaleDateString()}
            </Text>
          </Pressable>
        )}
        ListEmptyComponent={<Text style={[styles.empty, { color: c.textMuted }]}>{t("emptyFavorites")}</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  note: { padding: 12, fontSize: 13 },
  item: { padding: 16, borderBottomWidth: 1 },
  title: { fontWeight: "600", fontSize: 15 },
  date: { fontSize: 13, marginTop: 4 },
  empty: { padding: 24, textAlign: "center" },
});
