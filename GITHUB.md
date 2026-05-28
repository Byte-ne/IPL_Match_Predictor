# GitHub: 3 branches

```powershell
.\scripts\setup_branches.ps1
git remote add origin https://github.com/YOUR_USER/IPL_match_predictor.git
git push -u origin main docs site
```

- **docs** → GitHub Pages (root = HTML files)
- **site** → Deploy with `uvicorn api.main:app` (see site branch README)
