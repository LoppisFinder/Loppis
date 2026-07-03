# Deploy LoppisFinder API (one-time)

The Android app talks to a **hosted API on the internet**. Your phone does not need your PC running.

## 1. Create a PostGIS database

Use [Neon](https://neon.tech) (free tier) or [Supabase](https://supabase.com):

1. Create a new Postgres project.
2. In the SQL console run: `CREATE EXTENSION IF NOT EXISTS postgis;`
3. Copy the connection string and convert it for the API:
   - Replace `postgresql://` with `postgresql+asyncpg://`
   - Example: `postgresql+asyncpg://user:pass@ep-xxx.neon.tech/neondb?sslmode=require`

## 2. Deploy API to Render

1. Push this repo to GitHub.
2. Go to [Render Blueprints](https://dashboard.render.com/blueprints) → **New Blueprint Instance**.
3. Connect the repo — Render reads `render.yaml`.
4. In the service **Environment**, set `DATABASE_URL` to your Neon/Supabase URL (with `+asyncpg`).
5. Wait for deploy; open `https://<your-service>.onrender.com/health` — should return `{"status":"ok"}`.
6. Trigger an initial crawl: `POST https://<your-service>.onrender.com/v1/crawl/run`

## 3. Build the Android APK

```powershell
cd C:\temp\Cursor\Loppis\apps\mobile

# Set your deployed API URL (must match step 2)
$env:EXPO_PUBLIC_API_URL = "https://your-service.onrender.com"

# One-time: log in to Expo
npx eas-cli login

# One-time: link project (creates EAS project on expo.dev)
npx eas-cli init

# Cloud build — produces a downloadable APK (~10–20 min)
npx eas-cli build --platform android --profile preview --non-interactive
```

When the build finishes, EAS prints a download URL. Open it on your phone and install the APK.

## 4. Google Maps (optional)

Without a Maps API key the app still works but map tiles may be blank on some devices.

1. [Google Cloud Console](https://console.cloud.google.com) → enable **Maps SDK for Android**.
2. Create an API key restricted to Android app `se.loppisfinder.app`.
3. Set `EXPO_PUBLIC_GOOGLE_MAPS_API_KEY` before building.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| App shows fetch error | Check API `/health`; set correct `EXPO_PUBLIC_API_URL` and rebuild |
| Empty map | Add Google Maps API key and rebuild |
| Crawl slow on free tier | Render free tier sleeps after inactivity — first request wakes it (~30s) |
| Install blocked | Enable “Install unknown apps” for your browser/file manager |
