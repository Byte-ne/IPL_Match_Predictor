from __future__ import annotations
from datetime import date as Date
from typing import Any
import pandas as pd
from ..data.schema import CANON
from .elo import EloConfig, update_elo
from .rolling import RollingConfig, RollingTracker
from .state import ModelState

def build_features_and_state(matches: pd.DataFrame, use_matchday: bool) -> tuple[pd.DataFrame, ModelState]:
    elo_cfg, roll_cfg = EloConfig(), RollingConfig()
    tracker, ratings, venue_city = RollingTracker(roll_cfg), {}, {}
    rows = []
    for _, r in matches.iterrows():
        t1, t2, w = r[CANON.team1], r[CANON.team2], r[CANON.winner]
        v = r[CANON.venue]
        city = str(r.get(CANON.city, "") or "").strip()
        if city:
            venue_city[v] = city
        r1, r2 = ratings.get(t1, elo_cfg.base_rating), ratings.get(t2, elo_cfg.base_rating)
        feat = {
            "match_id": int(r[CANON.match_id]), "season": int(r[CANON.season]), "date": r[CANON.date],
            "team1": t1, "team2": t2, "venue": v, "city": city,
            "elo_team1": r1, "elo_team2": r2, "elo_diff": r1 - r2,
            "form_team1": tracker.team_form(t1), "form_team2": tracker.team_form(t2),
            "form_diff": tracker.team_form(t1) - tracker.team_form(t2),
            "h2h_team1_vs_team2": tracker.h2h_form(t1, t2),
            "y_team1_win": 1 if w == t1 else 0,
        }
        if use_matchday:
            feat["toss_winner"] = r.get(CANON.toss_winner, "")
            feat["toss_decision"] = r.get(CANON.toss_decision, "")
        rows.append(feat)
        tracker.update(t1, t2, w)
        s = 1.0 if w == t1 else 0.0
        nr1, nr2 = update_elo(r1, r2, s, elo_cfg.k)
        ratings[t1], ratings[t2] = float(nr1), float(nr2)
    feats = pd.DataFrame(rows)
    last = matches.iloc[-1]
    state = ModelState.from_tracker(ratings, tracker, elo_cfg, venue_city, int(last[CANON.season]), str(last[CANON.date]), len(matches))
    return feats, state

def features_for_matchup(state, team1, team2, venue, match_date: Date, toss_winner="", toss_decision="", use_matchday=False):
    tr = state.rolling_tracker()
    r1 = state.elo_ratings.get(team1, state.elo_config.base_rating)
    r2 = state.elo_ratings.get(team2, state.elo_config.base_rating)
    row = {
        "season": match_date.year, "team1": team1, "team2": team2, "venue": venue,
        "city": state.venue_city.get(venue, ""),
        "elo_team1": r1, "elo_team2": r2, "elo_diff": r1 - r2,
        "form_team1": tr.team_form(team1), "form_team2": tr.team_form(team2),
        "form_diff": tr.team_form(team1) - tr.team_form(team2),
        "h2h_team1_vs_team2": tr.h2h_form(team1, team2),
    }
    if use_matchday:
        row["toss_winner"] = toss_winner or ""
        row["toss_decision"] = (toss_decision or "").lower()
    return row
