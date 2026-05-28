from __future__ import annotations
from datetime import date as Date
from typing import Any
import pandas as pd
from ..config import Paths
from ..features.pipeline import features_for_matchup
from ..features.state import ModelState
from ..features.xi import XiHasherConfig, xi_diff_features
from .serialize import load_joblib
from ..api.cricapi import fetch_matchday_context

def _load(paths, mode):
    p = paths.artifacts_dir / ("matchday" if mode in {"matchday", "md"} else "pre") / "model.joblib"
    if not p.exists():
        raise FileNotFoundError(f"Missing model at {p}. Run: python -m ipl_predictor train {mode}")
    return load_joblib(p)

def _predict(model, cols, row):
    X = pd.DataFrame([row])[cols]
    for c in ("team1", "team2", "venue", "city", "toss_winner", "toss_decision"):
        if c in X.columns:
            X[c] = X[c].astype(str)
    p = float(model.predict_proba(X)[:, 1][0])
    return {"team1": row["team1"], "team2": row["team2"], "p_team1_win": p, "p_team2_win": 1 - p, "predicted_winner": row["team1"] if p >= 0.5 else row["team2"]}

def predict_prematch(paths, team1, team2, venue, date):
    art = _load(paths, "pre")
    state = art.get("state")
    if not isinstance(state, ModelState):
        raise FileNotFoundError("Retrain: python -m ipl_predictor train pre")
    row = features_for_matchup(state, team1, team2, venue, date, use_matchday=False)
    return _predict(art["model"], art["feature_cols"], row)

def predict_matchday(paths, fixture_id, team1, team2, venue, date, toss_winner, toss_decision, team1_xi, team2_xi):
    art = _load(paths, "matchday")
    state = art.get("state")
    if not isinstance(state, ModelState):
        raise FileNotFoundError("Retrain: python -m ipl_predictor train matchday")
    ctx = fetch_matchday_context(paths, fixture_id) if fixture_id else None
    t1 = team1 or (ctx.team1 if ctx else None)
    t2 = team2 or (ctx.team2 if ctx else None)
    v = venue or (ctx.venue if ctx else None)
    d = date or (ctx.date if ctx else None)
    tw = toss_winner or (ctx.toss_winner if ctx else "") if ctx else (toss_winner or "")
    td = (toss_decision or (ctx.toss_decision if ctx else "") if ctx else (toss_decision or "")).lower()
    if not (t1 and t2 and v and d):
        raise ValueError("Provide teams, venue, date or --fixture-id")
    row = features_for_matchup(state, t1, t2, v, d, tw, td, use_matchday=True)
    row.update({k: v for k, v in xi_diff_features(team1_xi, team2_xi, XiHasherConfig()).items() if k in art["feature_cols"]})
    out = _predict(art["model"], art["feature_cols"], row)
    out.update({"fixture_id": fixture_id, "data_through_season": state.last_season})
    return out
