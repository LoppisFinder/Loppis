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

**Important:** EAS commands must run from `apps/mobile`, not the repo root.

```powershell
$env:Path = "C:\Program Files\Git\bin;" + $env:Path
cd C:\temp\Cursor\Loppis\apps\mobile

$pnpm = "$env:APPDATA\npm\pnpm.cmd"
$env:EXPO_PUBLIC_API_URL = "https://loppisfinder-api.onrender.com"
$env:APP_VARIANT = "production"

# One-time: log in to Expo
& $pnpm dlx eas-cli login

# Verify EAS sees the project (should print @loppisfinder/loppisfinder)
& $pnpm dlx eas-cli project:info --non-interactive

# Cloud build — produces a downloadable APK (~10–20 min)
& $pnpm dlx eas-cli build --platform android --profile preview --non-interactive
```

Or from repo root (script `cd`s into `apps/mobile` for you):

```powershell
.\scripts\build-android-apk.ps1
```

When the build finishes, EAS prints a download URL. Open it on your phone and install the APK.

## 5. Deploy the web app to Azure

See **[AZURE-DEPLOY.md](./AZURE-DEPLOY.md)** for full steps (Container Registry + App Service).

After deploy:

1. Set `CORS_ORIGINS` on the Render API to your Azure URL (e.g. `https://loppisfinder-web.azurewebsites.net`).
2. Set `ADMIN_PASSWORD` on the Render API.
3. Open `https://<your-app>.azurewebsites.net/admin` to manage sources and crawls.

Public users only browse stored loppis — they cannot start crawls. When new data arrives, they see a refresh prompt.

## 6. Google Maps (optional)

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
| `EAS project not configured` | Run EAS from **`apps/mobile`**, not repo root. Check: `cd apps\mobile; pnpm dlx eas-cli project:info`. Do **not** run `eas init` at repo root — it creates stray `eas.json` / `app.json` there |
| Admin login fails | Set `ADMIN_PASSWORD` on the API and redeploy. Run DB migration (`alembic upgrade head` on deploy) |
| Web CORS error | Add your Azure web URL to API `CORS_ORIGINS` |
| Render deploy failed | Check **Logs** in Render dashboard. Set `DATABASE_URL` with `postgresql+asyncpg://` (Neon URL). Remove `channel_binding=require` from the URL if present. Enable PostGIS in Neon, then **Manual Deploy → Clear build cache & deploy** |
| Migration / SSL error | Use Neon **direct** connection string; PostGIS: `CREATE EXTENSION postgis;` |
