# GitHub Actions → Azure deployment

This pipeline builds the **LoppisFinder web app** Docker image, pushes it to **Azure Container Registry (ACR)**, and deploys it to **Azure App Service**.

The **API stays on Render** (`NEXT_PUBLIC_API_URL` is baked into the web build). Only the browser UI runs on Azure.

Workflow file: [`.github/workflows/azure-deploy.yml`](../.github/workflows/azure-deploy.yml)

---

## Part 1 — One-time Azure setup

Run in PowerShell after `az login`.

Replace names if already taken (ACR and Web App names must be **globally unique**).

```powershell
$RESOURCE_GROUP = "loppisfinder-rg"
$LOCATION = "westeurope"
$ACR_NAME = "loppisfinderacr"       # → loppisfinderacr.azurecr.io
$APP_NAME = "loppisfinder-web"
$API_URL = "https://loppisfinder-api.onrender.com"

# Resource group (skip if you already created it)
az group create --name $RESOURCE_GROUP --location $LOCATION

# Register providers (only needed once per subscription)
az provider register --namespace Microsoft.ContainerRegistry --wait
az provider register --namespace Microsoft.Web --wait

# Container registry
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# App Service plan + web app
az appservice plan create `
  --name loppisfinder-plan `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --is-linux `
  --sku B1

az webapp create `
  --resource-group $RESOURCE_GROUP `
  --plan loppisfinder-plan `
  --name $APP_NAME `
  --deployment-container-image-name nginx

az webapp config appsettings set `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --settings WEBSITES_PORT=3000
```

Your site will be: **`https://<APP_NAME>.azurewebsites.net`**

---

## Part 2 — Service principal for GitHub Actions

Still in PowerShell:

```powershell
$RESOURCE_GROUP = "loppisfinder-rg"
$SUBSCRIPTION_ID = az account show --query id -o tsv

az ad sp create-for-rbac `
  --name "github-loppisfinder-deploy" `
  --role contributor `
  --scopes "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP" `
  --sdk-auth
```

Copy the **entire JSON output** — that becomes the `AZURE_CREDENTIALS` secret.

Grant the service principal access to pull from ACR:

```powershell
$ACR_NAME = "loppisfinderacr"
$ACR_ID = az acr show --name $ACR_NAME --query id -o tsv
$SP_APP_ID = az ad sp list --display-name "github-loppisfinder-deploy" --query "[0].appId" -o tsv

az role assignment create --assignee $SP_APP_ID --role AcrPush --scope $ACR_ID
```

---

## Part 3 — GitHub repository secrets

Open: **https://github.com/LoppisFinder/Loppis/settings/secrets/actions**

Click **New repository secret** for each:

| Secret | Example value | Notes |
|--------|---------------|--------|
| `AZURE_CREDENTIALS` | Full JSON from `create-for-rbac --sdk-auth` | Entire `{ "clientId": ... }` block |
| `ACR_LOGIN_SERVER` | `loppisfinderacr.azurecr.io` | `{ACR_NAME}.azurecr.io` |
| `AZURE_WEBAPP_NAME` | `loppisfinder-web` | App Service name |
| `AZURE_RESOURCE_GROUP` | `loppisfinder-rg` | Resource group name |
| `NEXT_PUBLIC_API_URL` | `https://loppisfinder-api.onrender.com` | Render API URL |

No need for separate `ACR_USERNAME` / `ACR_PASSWORD` — the pipeline reads them from Azure during deploy.

---

## Part 4 — GitHub environment (optional but recommended)

1. Repo → **Settings** → **Environments** → **New environment** → name it **`production`**
2. Optionally add **Required reviewers** so deploys need approval
3. The workflow uses `environment: production`

If you skip creating the environment, GitHub creates it automatically on first run.

---

## Part 5 — Update Render API (CORS)

After the first successful web deploy, add your Azure URL to Render:

**Render** → API → **Environment** → `CORS_ORIGINS`:

```
http://localhost:3000,https://loppisfinder-web.azurewebsites.net
```

Replace with your actual `AZURE_WEBAPP_NAME`. Redeploy the API on Render.

---

## Part 6 — Run the pipeline

### Option A — Manual run (recommended first time)

1. Open **https://github.com/LoppisFinder/Loppis/actions**
2. Click **Deploy to Azure** in the left sidebar
3. Click **Run workflow**
4. Branch: **`main`**
5. Leave **Deploy web app** checked → **Run workflow**
6. Wait ~5–10 minutes; green check = success
7. Open **https://\<AZURE_WEBAPP_NAME\>.azurewebsites.net**

### Option B — Automatic on push

The pipeline also runs when you push to `main` and change:

- `apps/web/**`
- `packages/shared/**`
- `infra/Dockerfile.web-prod`
- `.github/workflows/azure-deploy.yml`

---

## Verify deployment

| Check | URL |
|-------|-----|
| Public map | `https://<APP_NAME>.azurewebsites.net` |
| Admin | `https://<APP_NAME>.azurewebsites.net/admin` |
| Azure logs | Portal → App Service → **Log stream** |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Yellow **Node.js 20 is deprecated** banner | Harmless on GitHub-hosted runners; workflow uses `checkout@v5` and `azure/login@v3` for Node 24 |
| `Missing AZURE_CREDENTIALS` | Add all secrets from Part 3 to the **`production`** environment |
| `MissingSubscriptionRegistration` | Run `az provider register --namespace Microsoft.ContainerRegistry --wait` |
| Pipeline OK but site blank | Check `NEXT_PUBLIC_API_URL` secret; re-run workflow |
| CORS errors in browser | Add Azure URL to Render `CORS_ORIGINS` |
| `Login failed` with `az acr login` in Actions | Ensure service principal has **AcrPush** on the registry |
| Container pull failed on App Service | Re-run pipeline (it sets ACR credentials on the Web App each time) |

---

## What is not deployed by this pipeline

| Service | Host |
|---------|------|
| API + crawler + DB migrations | **Render** (see [DEPLOY.md](./DEPLOY.md)) |
| Android APK | **EAS** (see [DEPLOY.md](./DEPLOY.md)) |

To deploy API to Azure later, a separate workflow and App Service would be needed.
