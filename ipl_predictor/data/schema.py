from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class CanonicalColumns:
    match_id: str = "match_id"
    season: str = "season"
    city: str = "city"
    date: str = "date"
    team1: str = "team1"
    team2: str = "team2"
    toss_winner: str = "toss_winner"
    toss_decision: str = "toss_decision"
    result: str = "result"
    dl_applied: str = "dl_applied"
    winner: str = "winner"
    venue: str = "venue"


CANON = CanonicalColumns()


def _first_existing(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    return None


def normalize_matches_df(df: pd.DataFrame) -> pd.DataFrame:
    col_map: dict[str, str] = {}
    for src, dst in [
        (["match_id", "id", "ID"], CANON.match_id),
        (["season", "Season"], CANON.season),
        (["city", "City"], CANON.city),
        (["date", "Date", "match_date"], CANON.date),
        (["team1", "Team1"], CANON.team1),
        (["team2", "Team2"], CANON.team2),
        (["venue", "Venue"], CANON.venue),
        (["toss_winner", "TossWinner"], CANON.toss_winner),
        (["toss_decision", "TossDecision"], CANON.toss_decision),
        (["result", "Result", "method"], CANON.result),
        (["dl_applied", "DLApplied"], CANON.dl_applied),
        (["winner", "WinningTeam", "Winner"], CANON.winner),
    ]:
        col = _first_existing(df, src)
        if col:
            col_map[col] = dst
    out = df.rename(columns=col_map).copy()
    required = [CANON.match_id, CANON.season, CANON.date, CANON.team1, CANON.team2, CANON.venue, CANON.winner]
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    out[CANON.match_id] = pd.to_numeric(out[CANON.match_id], errors="coerce").astype("Int64")
    out[CANON.season] = pd.to_numeric(out[CANON.season], errors="coerce").astype("Int64")
    parsed = pd.to_datetime(out[CANON.date], errors="coerce", dayfirst=True)
    if parsed.isna().any():
        parsed = pd.to_datetime(out[CANON.date], errors="coerce", dayfirst=False)
    out[CANON.date] = parsed.dt.date
    if out[CANON.date].isna().any():
        raise ValueError("Invalid dates in dataset")
    for c in [CANON.team1, CANON.team2, CANON.venue, CANON.winner]:
        out[c] = out[c].astype(str).str.strip()
    out[CANON.city] = out[CANON.city].astype(str).str.strip().replace({"nan": ""}) if CANON.city in out.columns else ""
    for c in [CANON.toss_winner, CANON.toss_decision, CANON.result]:
        if c not in out.columns:
            out[c] = ""
        else:
            out[c] = out[c].astype(str).str.strip().str.lower().replace({"nan": ""})
    if CANON.dl_applied not in out.columns:
        out[CANON.dl_applied] = 0
    out = out[~out[CANON.result].isin({"no result", "abandoned"})].copy()
    out = out[out[CANON.winner].astype(str).str.strip() != ""].copy()
    out = out[out[CANON.team1] != out[CANON.team2]].copy()
    return out.sort_values([CANON.date, CANON.match_id]).reset_index(drop=True)


def load_and_normalize_matches_csv(path: Path) -> pd.DataFrame:
    return normalize_matches_df(pd.read_csv(path))
