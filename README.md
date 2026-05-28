# IPLp — IPL Match Predictor

| Branch | Contents |
|--------|----------|
| `main` | ML package + CLI |
| `docs` | Static documentation (GitHub Pages) |
| `site` | Web UI + HTTP API |

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m ipl_predictor download-data --force
python -m ipl_predictor train pre
python -m ipl_predictor train matchday
```

Web (local): `pip install -r requirements-api.txt` then `uvicorn web.api.main:app --port 8000`

See [GITHUB.md](GITHUB.md) and [BEGINNER_SETUP.md](BEGINNER_SETUP.md).
