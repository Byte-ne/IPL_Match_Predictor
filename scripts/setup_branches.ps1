# Creates main, docs, site branches. NEVER deletes .git
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
$Backup = Join-Path $env:TEMP "iplp_backup_$(Get-Random)"
New-Item -ItemType Directory -Path $Backup | Out-Null
Copy-Item -Recurse docs, web, ipl_predictor, requirements.txt, requirements-api.txt, README.md, GITHUB.md, BEGINNER_SETUP.md, .gitignore, scripts, artifacts, data -Destination $Backup -ErrorAction SilentlyContinue

if (-not (Test-Path ".git")) { git init -b main }
git checkout -B main
git add ipl_predictor requirements.txt requirements-api.txt README.md GITHUB.md BEGINNER_SETUP.md .gitignore scripts docs web
git add artifacts/pre/model.joblib artifacts/matchday/model.joblib artifacts/*/*.json data/raw -f 2>$null
git commit -m "IPLp monorepo" 2>$null

# docs branch
$DocsTmp = Join-Path $env:TEMP "iplp_docs_$(Get-Random)"
Copy-Item -Recurse (Join-Path $Backup "docs") $DocsTmp
git checkout --orphan docs
Get-ChildItem -Force | Where-Object { $_.Name -ne '.git' } | Remove-Item -Recurse -Force
Copy-Item -Recurse "$DocsTmp\*" .
git add -A
git commit -m "IPLp docs site"
git checkout main

# site branch
$SiteTmp = Join-Path $env:TEMP "iplp_site_$(Get-Random)"
New-Item -ItemType Directory -Path $SiteTmp | Out-Null
Copy-Item -Recurse (Join-Path $Backup "web\api") (Join-Path $SiteTmp "api")
Copy-Item -Recurse (Join-Path $Backup "web\public") (Join-Path $SiteTmp "public")
Copy-Item (Join-Path $Backup "web\README.md") $SiteTmp
Copy-Item (Join-Path $Backup "requirements.txt") $SiteTmp
Copy-Item (Join-Path $Backup "requirements-api.txt") $SiteTmp
Copy-Item -Recurse (Join-Path $Backup "ipl_predictor") (Join-Path $SiteTmp "ipl_predictor")
Copy-Item -Recurse (Join-Path $Backup "artifacts") (Join-Path $SiteTmp "artifacts")
New-Item -ItemType Directory -Path (Join-Path $SiteTmp "data\raw") -Force | Out-Null
Copy-Item (Join-Path $Backup "data\raw\*") (Join-Path $SiteTmp "data\raw")
"@.venv/`n__pycache__/`nartifacts/catboost_logs/" | Set-Content (Join-Path $SiteTmp ".gitignore")

git checkout --orphan site
Get-ChildItem -Force | Where-Object { $_.Name -ne '.git' } | Remove-Item -Recurse -Force
Copy-Item -Recurse "$SiteTmp\*" .
git add -A
git commit -m "IPLp web + API"
git checkout main
Copy-Item -Recurse "$Backup\*" $Root -Force
Write-Host "Done. Branches: main, docs, site"
git branch
