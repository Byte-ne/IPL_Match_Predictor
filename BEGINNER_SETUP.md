# Beginner setup — what YOU need

## 1) Python 3.12
Install from python.org. Check: `py -3.12 --version`

## 2) Project setup
```powershell
cd "C:\Users\kilob\OneDrive\Desktop\IPL_match_predictor"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-api.txt
```

## 3) Data + train
```powershell
python -m ipl_predictor download-data --force
python -m ipl_predictor train pre
python -m ipl_predictor train matchday
```

## 4) Web app (no CLI for users)
```powershell
$env:IPL_PROJECT_ROOT = (Get-Location).Path
uvicorn web.api.main:app --port 8000
```
Open http://127.0.0.1:8000

## 5) CricAPI (optional, CLI only)
```powershell
$env:CRICAPI_KEY="your_key"
python -m ipl_predictor list-fixtures
```

## 6) GitHub
```powershell
.\scripts\setup_branches.ps1
git remote add origin https://github.com/YOUR_USER/IPL_match_predictor.git
git push -u origin main docs site
```
Enable Pages on branch `docs`.
