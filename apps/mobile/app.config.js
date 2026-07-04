/** @type {import('expo/config').ExpoConfig} */
const isProduction = process.env.APP_VARIANT === "production";

module.exports = {
  name: "LoppisFinder",
  slug: "loppisfinder",
  version: "1.0.0",
  orientation: "portrait",
  scheme: "loppisfinder",
  userInterfaceStyle: "automatic",
  icon: "./assets/icon.png",
  experiments: {
    tsconfigPaths: true,
  },  plugins: ["expo-router", "expo-location", "expo-notifications", "expo-secure-store"],
  android: {
    adaptiveIcon: {
      foregroundImage: "./assets/adaptive-icon.png",
      backgroundColor: "#2563eb",
    },
    package: "se.loppisfinder.app",
    permissions: ["ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION"],
    usesCleartextTraffic: !isProduction,
    config: {
      googleMaps: {
        apiKey: process.env.EXPO_PUBLIC_GOOGLE_MAPS_API_KEY ?? "",
      },
    },
  },
  extra: {
    eas: {
      projectId: "7574a2c7-11c2-43c7-b087-78e0aa767069",
    },
    apiUrl:
      process.env.EXPO_PUBLIC_API_URL ??
      (isProduction ? "https://loppisfinder-api.onrender.com" : "http://10.0.2.2:8000"),
  },
};
