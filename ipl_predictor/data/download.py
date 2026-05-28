from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

from .schema import CANON, normalize_matches_df

PRIMARY_MATCHES_CSV_URL = (
    "https://raw.githubusercontent.com/Kkarthik092000/Ipl-Analysis-project/main/"
    "ipl%202008-2024%20matches.csv"
)
LEGACY_MATCHES_CSV_URL = (
    "https://raw.githubusercontent.com/12345k/IPL-Dataset/master/IPL/data.csv"
)
DATASET_URLS = [PRIMARY_MATCHES_CSV_URL, LEGACY_MATCHES_CSV_URL]


def _validate_matches_csv(path: Path) -> dict[str, int | str]:
    df = pd.read_csv(path)
    norm = normalize_matches_df(df)
    seasons = norm[CANON.season].dropna().astype(int)
    return {
        "rows": int(len(norm)),
        "min_season": int(seasons.min()) if len(seasons) else 0,
        "max_season": int(seasons.max()) if len(seasons) else 0,
    }


def download_default_dataset(raw_dir: Path, force: bool = False) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path = raw_dir / "matches.csv"
    meta_path = raw_dir / "dataset_meta.json"
    if out_path.exists() and not force:
        return out_path
    last_error: Exception | None = None
    for url in DATASET_URLS:
        try:
            resp = requests.get(url, timeout=90)
            resp.raise_for_status()
            tmp = out_path.with_suffix(".csv.tmp")
            tmp.write_bytes(resp.content)
            info = _validate_matches_csv(tmp)
            if info["rows"] < 100:
                raise ValueError(f"Dataset too small ({info['rows']} rows)")
            tmp.replace(out_path)
            meta_path.write_text(json.dumps({"source_url": url, **info}, indent=2), encoding="utf-8")
            return out_path
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Failed to download dataset. Last error: {last_error}")


def read_dataset_meta(raw_dir: Path) -> dict | None:
    meta_path = raw_dir / "dataset_meta.json"
    if not meta_path.exists():
        return None
    return json.loads(meta_path.read_text(encoding="utf-8"))
