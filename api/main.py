from __future__ import annotations

import os
import sys
from datetime import date as Date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

API_DIR = Path(__file__).resolve().parent
SITE_DIR = API_DIR.parent

def _detect_project_root() -> Path:
    env = os.getenv("IPL_PROJECT_ROOT")
    if env:
        return Path(env)
    if (SITE_DIR / "ipl_predictor").is_dir():
        return SITE_DIR
    if (SITE_DIR.parent / "ipl_predictor").is_dir():
        return SITE_DIR.parent
    return SITE_DIR.parent


PROJECT_ROOT = _detect_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("IPL_PROJECT_ROOT", str(PROJECT_ROOT))

from ipl_predictor.config import get_paths  # noqa: E402
from ipl_predictor.data.info import dataset_report  # noqa: E402
from ipl_predictor.data.schema import CANON, load_and_normalize_matches_csv  # noqa: E402
from ipl_predictor.models.predict import predict_matchday, predict_prematch  # noqa: E402

PUBLIC_DIR = SITE_DIR / "public"

app = FastAPI(
    title="IPLp Predictor API",
    description="Public HTTP API for IPL pre-match and match-day win probabilities.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PreMatchBody(BaseModel):
    team1: str = Field(..., min_length=1)
    team2: str = Field(..., min_length=1)
    venue: str = Field(..., min_length=1)
    date: str = Field(..., description="YYYY-MM-DD")


class MatchDayBody(PreMatchBody):
    toss_winner: str = ""
    toss_decision: str = Field("", description="bat or field")
    team1_xi: str = Field("", description="Optional comma-separated player names")
    team2_xi: str = Field("", description="Optional comma-separated player names")


@app.get("/api/health")
def health() -> dict:
    paths = get_paths()
    pre_ok = (paths.artifacts_dir / "pre" / "model.joblib").exists()
    md_ok = (paths.artifacts_dir / "matchday" / "model.joblib").exists()
    return {
        "status": "ok" if pre_ok and md_ok else "degraded",
        "pre_model": pre_ok,
        "matchday_model": md_ok,
        "project_root": str(paths.project_root),
    }


@app.get("/api/meta/dataset")
def meta_dataset() -> dict:
    return dataset_report(get_paths())


@app.get("/api/meta/teams")
def meta_teams() -> dict:
    paths = get_paths()
    csv_path = paths.raw_dir / "matches.csv"
    if not csv_path.exists():
        raise HTTPException(503, "Dataset not available on server.")
    df = load_and_normalize_matches_csv(csv_path)
    teams = sorted(set(df[CANON.team1]).union(set(df[CANON.team2])))
    return {"teams": teams}


@app.get("/api/meta/venues")
def meta_venues() -> dict:
    paths = get_paths()
    csv_path = paths.raw_dir / "matches.csv"
    if not csv_path.exists():
        raise HTTPException(503, "Dataset not available on server.")
    df = load_and_normalize_matches_csv(csv_path)
    venues = sorted(df[CANON.venue].dropna().unique().tolist())
    return {"venues": venues}


@app.post("/api/predict/pre")
def api_predict_pre(body: PreMatchBody) -> dict:
    try:
        d = Date.fromisoformat(body.date)
    except ValueError as exc:
        raise HTTPException(400, "date must be YYYY-MM-DD") from exc
    try:
        return predict_prematch(
            paths=get_paths(),
            team1=body.team1.strip(),
            team2=body.team2.strip(),
            venue=body.venue.strip(),
            date=d,
        )
    except FileNotFoundError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@app.post("/api/predict/matchday")
def api_predict_matchday(body: MatchDayBody) -> dict:
    try:
        d = Date.fromisoformat(body.date)
    except ValueError as exc:
        raise HTTPException(400, "date must be YYYY-MM-DD") from exc
    try:
        return predict_matchday(
            paths=get_paths(),
            fixture_id=None,
            team1=body.team1.strip(),
            team2=body.team2.strip(),
            venue=body.venue.strip(),
            date=d,
            toss_winner=body.toss_winner.strip() or None,
            toss_decision=body.toss_decision.strip() or None,
            team1_xi=body.team1_xi.strip() or None,
            team2_xi=body.team2_xi.strip() or None,
        )
    except FileNotFoundError as exc:
        raise HTTPException(503, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc


@app.get("/")
def index() -> FileResponse:
    index_path = PUBLIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(404, "Frontend not found.")
    return FileResponse(index_path)


if PUBLIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")
