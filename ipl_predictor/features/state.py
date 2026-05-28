from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import Any
from .elo import EloConfig
from .rolling import RollingConfig, RollingTracker

@dataclass
class ModelState:
    elo_ratings: dict[str, float] = field(default_factory=dict)
    elo_config: EloConfig = field(default_factory=EloConfig)
    rolling_config: RollingConfig = field(default_factory=RollingConfig)
    team_results: dict[str, list[int]] = field(default_factory=dict)
    h2h_results: dict[str, list[int]] = field(default_factory=dict)
    venue_city: dict[str, str] = field(default_factory=dict)
    last_season: int = 0
    last_date: str = ""
    match_count: int = 0

    def rolling_tracker(self) -> RollingTracker:
        t = RollingTracker(self.rolling_config)
        for team, res in self.team_results.items():
            t.team_results[team] = deque(res, maxlen=self.rolling_config.form_window)
        for key, res in self.h2h_results.items():
            a, b = key.split("|||")
            t.h2h_results[(a, b)] = deque(res, maxlen=self.rolling_config.h2h_window)
        return t

    @classmethod
    def from_tracker(cls, ratings, tracker, elo_cfg, venue_city, last_season, last_date, match_count):
        h2h = {f"{k[0]}|||{k[1]}": list(v) for k, v in tracker.h2h_results.items()}
        team_res = {team: list(v) for team, v in tracker.team_results.items()}
        return cls(
            elo_ratings=dict(ratings), elo_config=elo_cfg, rolling_config=tracker.cfg,
            team_results=team_res, h2h_results=h2h, venue_city=dict(venue_city),
            last_season=last_season, last_date=last_date, match_count=match_count,
        )
