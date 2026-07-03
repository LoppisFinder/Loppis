import * as SecureStore from "expo-secure-store";
export type Locale = "sv" | "en";

export const translations = {
  sv: {
    appTitle: "LoppisFinder",
    countLoppis: "{count} loppis",
    fetchReal: "Hämta riktiga loppis",
    fetching: "Hämtar…",
    crawlStart: "Söker loppis på webben…",
    crawlDone: "Hämtade {ingested} nya ({discovered} hittade)",
    crawlFail: "Kunde inte starta crawl",
    fetchError: "Kunde inte hämta loppis. Kontrollera API-anslutning.",
    period: "Period",
    radius: "Radie",
    radiusKm: "{km} km",
    minReliability: "Min. pålitlighet",
    myLocation: "Min plats",
    mapHint: "Tryck på kartan eller dra den röda markören",
    wholeMonth: "Hela månaden",
    wholeYear: "Hela året",
    currentMonth: "Denna månad",
    selectEndDate: " — välj slutdatum",
    monthView: "Månadsvy",
    loppisCount: "{count} loppis",
    loadingList: "Laddar…",
    emptyList: "Inga loppis i detta område.",
    favorites: "Favoriter",
    favoritesNote: "Sparad på denna enhet — anonym session",
    emptyFavorites: "Inga favoriter ännu",
    back: "← Tillbaka",
    whyScore: "Varför detta betyg?",
    scoreSource: "Källans tillförlitlighet",
    scoreConfirm: "Bekräftelser",
    scoreFeedback: "Omdömen",
    scoreHistory: "Historik",
    scoreFresh: "Aktualitet",
    sources: "Källor",
    history: "Historik",
    happened: "Ägde rum",
    cancelledEvent: "Inställd",
    favorite: "★ Favorit",
    addFavorite: "☆ Lägg till favorit",
    addCalendar: "Lägg till kalender",
    alertBefore24: "24h innan",
    createAlert: "Skapa påminnelse (24h)",
    alertCreated: "Påminnelse skapad!",
    language: "Språk",
    theme: "Tema",
    reliability: {
      cancelled: "Inställd",
      trusted: "Pålitlig",
      uncertain: "Osäker",
      unverified: "Overifierad",
    },
  },
  en: {
    appTitle: "LoppisFinder",
    countLoppis: "{count} listings",
    fetchReal: "Fetch listings",
    fetching: "Fetching…",
    crawlStart: "Searching for flea markets…",
    crawlDone: "Fetched {ingested} new ({discovered} found)",
    crawlFail: "Could not start crawl",
    fetchError: "Could not load listings. Check API connection.",
    period: "Period",
    radius: "Radius",
    radiusKm: "{km} km",
    minReliability: "Min. reliability",
    myLocation: "My location",
    mapHint: "Tap the map or drag the red pin",
    wholeMonth: "Whole month",
    wholeYear: "Whole year",
    currentMonth: "Current month",
    selectEndDate: " — pick end date",
    monthView: "Month view",
    loppisCount: "{count} listings",
    loadingList: "Loading…",
    emptyList: "No listings in this area.",
    favorites: "Favorites",
    favoritesNote: "Saved on this device — anonymous session",
    emptyFavorites: "No favorites yet",
    back: "← Back",
    whyScore: "Why this score?",
    scoreSource: "Source trust",
    scoreConfirm: "Confirmations",
    scoreFeedback: "Feedback",
    scoreHistory: "History",
    scoreFresh: "Freshness",
    sources: "Sources",
    history: "History",
    happened: "Took place",
    cancelledEvent: "Cancelled",
    favorite: "★ Favorite",
    addFavorite: "☆ Add to favorites",
    addCalendar: "Add to calendar",
    alertBefore24: "24h before",
    createAlert: "Create reminder (24h)",
    alertCreated: "Reminder created!",
    language: "Language",
    theme: "Theme",
    reliability: {
      cancelled: "Cancelled",
      trusted: "Reliable",
      uncertain: "Uncertain",
      unverified: "Unverified",
    },
  },
} as const;

const LOCALE_KEY = "loppis_locale";

function getNested(obj: Record<string, unknown>, path: string): string | undefined {
  let cur: unknown = obj;
  for (const part of path.split(".")) {
    if (cur && typeof cur === "object" && part in (cur as Record<string, unknown>)) {
      cur = (cur as Record<string, unknown>)[part];
    } else return undefined;
  }
  return typeof cur === "string" ? cur : undefined;
}

export function translate(
  locale: Locale,
  key: string,
  vars?: Record<string, string | number>
): string {
  const raw = getNested(translations[locale] as Record<string, unknown>, key) ?? key;
  if (!vars) return raw;
  return Object.entries(vars).reduce(
    (acc, [k, v]) => acc.replace(new RegExp(`\\{${k}\\}`, "g"), String(v)),
    raw
  );
}

export async function loadStoredLocale(): Promise<Locale> {
  const stored = await SecureStore.getItemAsync(LOCALE_KEY);
  return stored === "en" ? "en" : "sv";
}

export async function saveLocale(locale: Locale): Promise<void> {
  await SecureStore.setItemAsync(LOCALE_KEY, locale);
}

export function reliabilityLabel(
  locale: Locale,
  score: number,
  status: string
): string {
  if (status === "cancelled") return translate(locale, "reliability.cancelled");
  if (score >= 70) return translate(locale, "reliability.trusted");
  if (score >= 40) return translate(locale, "reliability.uncertain");
  return translate(locale, "reliability.unverified");
}
