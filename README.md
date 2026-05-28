# IPLp Web

Public FastAPI + static frontend (`web/` on `main`, branch root on `site`).

```powershell
pip install -r requirements-api.txt
$env:IPL_PROJECT_ROOT = (Get-Location).Path
uvicorn web.api.main:app --reload --port 8000
```

Open http://127.0.0.1:8000
