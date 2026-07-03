export const DEFAULT_RADIUS_KM = 100;
export const MIN_RADIUS_KM = 5;
export const MAX_RADIUS_KM = 200;

export const SWEDEN_CENTER = { lat: 62.0, lng: 15.0 };
export const STOCKHOLM = { lat: 59.3293, lng: 18.0686 };

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  process.env.EXPO_PUBLIC_API_URL ??
  "http://localhost:8000";

export const SOURCE_TRUST_WEIGHTS: Record<string, number> = {
  website: 80,
  reddit: 60,
  facebook: 55,
  instagram: 50,
  forum: 40,
  user_submission: 45,
};
