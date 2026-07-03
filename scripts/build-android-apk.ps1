param(
  [string]$ApiUrl = $env:EXPO_PUBLIC_API_URL,
  [ValidateSet("preview", "production")]
  [string]$Profile = "preview"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$MobileRoot = Join-Path $RepoRoot "apps\mobile"
$Pnpm = Join-Path $env:APPDATA "npm\pnpm.cmd"

if (-not (Test-Path $Pnpm)) {
  throw "pnpm not found. Install Node.js LTS and run: npm install -g pnpm"
}

if (-not $ApiUrl) {
  $ApiUrl = "https://loppisfinder-api.onrender.com"
  Write-Host "Using default API URL: $ApiUrl"
  Write-Host "Set EXPO_PUBLIC_API_URL or pass -ApiUrl to your deployed API."
}

$env:EXPO_PUBLIC_API_URL = $ApiUrl
$env:APP_VARIANT = "production"

Push-Location $MobileRoot
try {
  Write-Host "Checking Expo login..."
  & $Pnpm dlx eas-cli@latest whoami 2>&1 | Out-String | Write-Host
  if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Not logged in to Expo. Run once:"
    Write-Host "  cd apps\mobile"
    Write-Host "  pnpm dlx eas-cli login"
    Write-Host "  pnpm dlx eas-cli init"
    throw "Expo login required before building APK."
  }

  Write-Host "Starting EAS Android build (profile: $Profile)..."
  Write-Host "API URL baked into app: $ApiUrl"
  & $Pnpm dlx eas-cli@latest build `
    --platform android `
    --profile $Profile `
    --non-interactive

  if ($LASTEXITCODE -ne 0) {
    throw "EAS build failed with exit code $LASTEXITCODE"
  }

  Write-Host ""
  Write-Host "When complete, download the APK from the URL above and install on your phone."
} finally {
  Pop-Location
}
