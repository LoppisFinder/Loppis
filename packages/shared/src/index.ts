import { z } from "zod";

export const LoppisStatus = z.enum([
  "upcoming",
  "cancelled",
  "past",
  "unverified",
]);
export type LoppisStatus = z.infer<typeof LoppisStatus>;

export const SourceType = z.enum([
  "facebook",
  "instagram",
  "reddit",
  "forum",
  "website",
  "user_submission",
]);
export type SourceType = z.infer<typeof SourceType>;

export const LoppisSourceSchema = z.object({
  id: z.string().uuid(),
  source_type: SourceType,
  source_url: z.string().url(),
  raw_snippet: z.string().nullable(),
  crawled_at: z.string().datetime(),
  source_weight: z.number(),
});
export type LoppisSource = z.infer<typeof LoppisSourceSchema>;

export const ScoreBreakdownSchema = z.object({
  source_trust: z.number(),
  confirmation_count: z.number(),
  feedback_sentiment: z.number(),
  historical_accuracy: z.number(),
  freshness: z.number(),
  cancellation_penalty: z.number(),
  total: z.number(),
});
export type ScoreBreakdown = z.infer<typeof ScoreBreakdownSchema>;

export const LoppisSummarySchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  description: z.string().nullable(),
  start_at: z.string().datetime(),
  end_at: z.string().datetime().nullable(),
  lat: z.number(),
  lng: z.number(),
  address_text: z.string().nullable(),
  municipality: z.string().nullable(),
  county: z.string().nullable(),
  reliability_score: z.number(),
  status: LoppisStatus,
  cover_image_url: z.string().nullable(),
  tags: z.array(z.string()),
  source_count: z.number().optional(),
});
export type LoppisSummary = z.infer<typeof LoppisSummarySchema>;

export const LoppisHistorySchema = z.object({
  id: z.string().uuid(),
  occurred_at: z.string().datetime(),
  was_accurate: z.boolean(),
  photo_urls: z.array(z.string()),
  attendance_signal: z.string().nullable(),
});
export type LoppisHistory = z.infer<typeof LoppisHistorySchema>;

export const LoppisDetailSchema = LoppisSummarySchema.extend({
  is_recurring: z.boolean(),
  sources: z.array(LoppisSourceSchema),
  history: z.array(LoppisHistorySchema),
  score_breakdown: ScoreBreakdownSchema,
});
export type LoppisDetail = z.infer<typeof LoppisDetailSchema>;

export const LoppisListQuerySchema = z.object({
  lat: z.number(),
  lng: z.number(),
  radius_km: z.number().min(1).max(200).default(25),
  from: z.string().datetime().optional(),
  to: z.string().datetime().optional(),
  min_score: z.number().min(0).max(100).default(0),
});
export type LoppisListQuery = z.infer<typeof LoppisListQuerySchema>;

export const AnonymousSessionSchema = z.object({
  anonymous_user_id: z.string().uuid(),
  access_token: z.string(),
  expires_at: z.string().datetime(),
});
export type AnonymousSession = z.infer<typeof AnonymousSessionSchema>;

export const FavoriteSchema = z.object({
  id: z.string().uuid(),
  loppis_id: z.string().uuid(),
  created_at: z.string().datetime(),
  loppis: LoppisSummarySchema.optional(),
});
export type Favorite = z.infer<typeof FavoriteSchema>;

export const AlertSchema = z.object({
  id: z.string().uuid(),
  loppis_id: z.string().uuid().nullable(),
  radius_km: z.number().nullable(),
  before_hours: z.number(),
  min_score: z.number(),
  created_at: z.string().datetime(),
});
export type Alert = z.infer<typeof AlertSchema>;

export const ReportType = z.enum([
  "cancelled",
  "wrong_date",
  "wrong_location",
  "spam",
  "other",
]);
export type ReportType = z.infer<typeof ReportType>;

export const MetaSchema = z.object({
  data_version: z.string(),
  last_crawl_at: z.string().nullable(),
  total_loppis: z.number(),
});
export type Meta = z.infer<typeof MetaSchema>;

export function reliabilityLabel(score: number, status: LoppisStatus): string {
  if (status === "cancelled") return "Inställd";
  if (score >= 70) return "Pålitlig";
  if (score >= 40) return "Osäker";
  return "Overifierad";
}

export class LoppisApiClient {
  constructor(private baseUrl: string, private token?: string) {}

  setToken(token: string) {
    this.token = token;
  }

  private headers(): HeadersInit {
    const h: HeadersInit = { "Content-Type": "application/json" };
    if (this.token) h["Authorization"] = `Bearer ${this.token}`;
    return h;
  }

  async createAnonymousSession(): Promise<AnonymousSession> {
    const res = await fetch(`${this.baseUrl}/v1/session/anonymous`, {
      method: "POST",
      headers: this.headers(),
    });
    if (!res.ok) throw new Error(`Session failed: ${res.status}`);
    return AnonymousSessionSchema.parse(await res.json());
  }

  async getMeta(): Promise<Meta> {
    const res = await fetch(`${this.baseUrl}/v1/meta`);
    if (!res.ok) throw new Error(`Meta failed: ${res.status}`);
    return MetaSchema.parse(await res.json());
  }

  async listLoppis(query: LoppisListQuery): Promise<LoppisSummary[]> {
    const params = new URLSearchParams({
      lat: String(query.lat),
      lng: String(query.lng),
      radius_km: String(query.radius_km),
      min_score: String(query.min_score),
    });
    if (query.from) params.set("from", query.from);
    if (query.to) params.set("to", query.to);
    const res = await fetch(`${this.baseUrl}/v1/loppis?${params}`);
    if (!res.ok) throw new Error(`List failed: ${res.status}`);
    return z.array(LoppisSummarySchema).parse(await res.json());
  }

  async getLoppis(id: string): Promise<LoppisDetail> {
    const res = await fetch(`${this.baseUrl}/v1/loppis/${id}`);
    if (!res.ok) throw new Error(`Get failed: ${res.status}`);
    return LoppisDetailSchema.parse(await res.json());
  }

  async getFavorites(): Promise<Favorite[]> {
    const res = await fetch(`${this.baseUrl}/v1/favorites`, {
      headers: this.headers(),
    });
    if (!res.ok) throw new Error(`Favorites failed: ${res.status}`);
    return z.array(FavoriteSchema).parse(await res.json());
  }

  async addFavorite(loppisId: string): Promise<Favorite> {
    const res = await fetch(`${this.baseUrl}/v1/favorites`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({ loppis_id: loppisId }),
    });
    if (!res.ok) throw new Error(`Add favorite failed: ${res.status}`);
    return FavoriteSchema.parse(await res.json());
  }

  async removeFavorite(id: string): Promise<void> {
    const res = await fetch(`${this.baseUrl}/v1/favorites/${id}`, {
      method: "DELETE",
      headers: this.headers(),
    });
    if (!res.ok) throw new Error(`Remove favorite failed: ${res.status}`);
  }

  async getAlerts(): Promise<Alert[]> {
    const res = await fetch(`${this.baseUrl}/v1/alerts`, {
      headers: this.headers(),
    });
    if (!res.ok) throw new Error(`Alerts failed: ${res.status}`);
    return z.array(AlertSchema).parse(await res.json());
  }

  async createAlert(data: {
    loppis_id?: string;
    radius_km?: number;
    before_hours: number;
    min_score?: number;
  }): Promise<Alert> {
    const res = await fetch(`${this.baseUrl}/v1/alerts`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`Create alert failed: ${res.status}`);
    return AlertSchema.parse(await res.json());
  }

  async reportLoppis(
    id: string,
    reportType: ReportType,
    text?: string
  ): Promise<void> {
    const res = await fetch(`${this.baseUrl}/v1/loppis/${id}/report`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({ report_type: reportType, text }),
    });
    if (!res.ok) throw new Error(`Report failed: ${res.status}`);
  }

  icsUrl(id: string): string {
    return `${this.baseUrl}/v1/loppis/${id}/ics`;
  }
}

export * from "./constants";
