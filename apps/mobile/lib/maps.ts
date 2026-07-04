import Constants from "expo-constants";
import { Platform } from "react-native";
import { PROVIDER_GOOGLE } from "react-native-maps";

export function getGoogleMapsApiKey(): string {
  const fromConfig = Constants.expoConfig?.android?.config?.googleMaps?.apiKey;
  if (typeof fromConfig === "string" && fromConfig.trim()) {
    return fromConfig.trim();
  }
  const fromEnv = process.env.EXPO_PUBLIC_GOOGLE_MAPS_API_KEY;
  if (typeof fromEnv === "string" && fromEnv.trim()) {
    return fromEnv.trim();
  }
  return "";
}

export function hasGoogleMapsKey(): boolean {
  return getGoogleMapsApiKey().length > 0;
}

export function getMapProvider() {
  if (Platform.OS === "android" && hasGoogleMapsKey()) {
    return PROVIDER_GOOGLE;
  }
  return undefined;
}
