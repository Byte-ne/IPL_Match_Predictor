from __future__ import annotations

from ..config import Paths
from .download import read_dataset_meta
from .schema import CANON, load_and_normalize_matches_csv


def dataset_report(paths: Paths) -> dict:
    raw_csv = paths.raw_dir / "matches.csv"
    if not raw_csv.exists():
        return {"exists": False, "message": "Run: python -m ipl_predictor download-data --force"}
    meta = read_dataset_meta(paths.raw_dir)
    matches = load_and_normalize_matches_csv(raw_csv)
    seasons = matches[CANON.season].astype(int)
    return {
        "exists": True,
        "path": str(raw_csv),
        "rows": int(len(matches)),
        "min_season": int(seasons.min()),
        "max_season": int(seasons.max()),
        "last_match_date": str(matches[CANON.date].iloc[-1]),
        "download_meta": meta,
    }
