# Deploy LoppisFinder Web to Azure

The web app is a Next.js container. The API stays on **Render** (or your own host) — only the browser-facing site runs on Azure.

## Prerequisites

- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) logged in (`az login`)
- Docker Desktop (to build locally) **or** GitHub Actions (see below)
- API deployed and healthy (see [DEPLOY.md](./DEPLOY.md))
- `ADMIN_PASSWORD` set on the API (Render dashboard → Environment)

## 1. One-time Azure setup

Replace placeholders:

```powershell
$RESOURCE_GROUP = "loppisfinder-rg"
$LOCATION = "westeurope"
$ACR_NAME = "loppisfinderacr"          # must be globally unique, lowercase
$APP_NAME = "loppisfinder-web"          # must be globally unique
$API_URL = "https://loppisfinder-api.onrender.com"

az group create --name $RESOURCE_GROUP --location $LOCATION

az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

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
```

## 2. Build and push the web image

From the **repo root**:

```powershell
cd C:\temp\Cursor\Loppis

$ACR_NAME = "loppisfinderacr"
$API_URL = "https://loppisfinder-api.onrender.com"

az acr login --name $ACR_NAME

docker build `
  -f infra/Dockerfile.web-prod `
  --build-arg NEXT_PUBLIC_API_URL=$API_URL `
  -t "$ACR_NAME.azurecr.io/loppisfinder-web:latest" .

docker push "$ACR_NAME.azurecr.io/loppisfinder-web:latest"
```

## 3. Point the Web App at the container

```powershell
$ACR_NAME = "loppisfinderacr"
$APP_NAME = "loppisfinder-web"
$RESOURCE_GROUP = "loppisfinder-rg"

$ACR_USER = az acr credential show --name $ACR_NAME --query username -o tsv
$ACR_PASS = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv

az webapp config container set `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --docker-custom-image-name "$ACR_NAME.azurecr.io/loppisfinder-web:latest" `
  --docker-registry-server-url "https://$ACR_NAME.azurecr.io" `
  --docker-registry-server-user $ACR_USER `
  --docker-registry-server-password $ACR_PASS

az webapp config appsettings set `
  --name $APP_NAME `
  --resource-group $RESOURCE_GROUP `
  --settings WEBSITES_PORT=3000

az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP
```

Your site: `https://<APP_NAME>.azurewebsites.net`

## 4. Allow the web origin in the API (CORS)

In **Render** → API service → Environment, set `CORS_ORIGINS` to your Azure URL (comma-separated if multiple):

```
https://loppisfinder-web.azurewebsites.net
```

Redeploy the API after changing CORS.

## 5. Admin access

1. Set a strong `ADMIN_PASSWORD` on the Render API.
2. Open `https://<APP_NAME>.azurewebsites.net/admin`
3. Log in with that password.
4. Add crawl sources, configure auto-crawl interval, run manual crawls.

Public users **cannot** start crawls — the crawl button was removed from the map page.

When a crawl finishes, visitors see **“Nya loppis finns tillgängliga”** and can refresh the list.

## 6. GitHub Actions (optional CI/CD)

Add these secrets to the GitHub repo:

| Secret | Value |
|--------|--------|
| `AZURE_CREDENTIALS` | JSON from `az ad sp create-for-rbac --sdk-auth` |
| `ACR_LOGIN_SERVER` | e.g. `loppisfinderacr.azurecr.io` |
| `ACR_USERNAME` | ACR admin username |
| `ACR_PASSWORD` | ACR admin password |
| `AZURE_WEBAPP_NAME` | e.g. `loppisfinder-web` |
| `NEXT_PUBLIC_API_URL` | Your Render API URL |

Workflow file: `.github/workflows/azure-web.yml` (builds and deploys on push to `main`).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Blank page / API errors | Rebuild with correct `NEXT_PUBLIC_API_URL` build arg |
| CORS error in browser | Add Azure URL to API `CORS_ORIGINS` |
| Admin login 503 | Set `ADMIN_PASSWORD` on Render API |
| Admin login 401 | Wrong password |
| Container won't start | Check Web App → Log stream; ensure `WEBSITES_PORT=3000` |
