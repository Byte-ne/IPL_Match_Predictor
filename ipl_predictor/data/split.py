from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .schema import CANON


@dataclass(frozen=True)
class TimeSplit:
    train: pd.DataFrame
    valid: pd.DataFrame


def time_split_by_season(df: pd.DataFrame, valid_seasons: int = 2) -> TimeSplit:
    seasons = sorted([int(s) for s in df[CANON.season].dropna().unique()])
    if len(seasons) < valid_seasons + 1:
        raise ValueError(f"Not enough seasons ({len(seasons)})")
    valid_set = set(seasons[-valid_seasons:])
    return TimeSplit(
        train=df[~df[CANON.season].isin(valid_set)].copy(),
        valid=df[df[CANON.season].isin(valid_set)].copy(),
    )
