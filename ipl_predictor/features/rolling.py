from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass

@dataclass(frozen=True)
class RollingConfig:
    form_window: int = 8
    h2h_window: int = 10

class RollingTracker:
    def __init__(self, cfg: RollingConfig):
        self.cfg = cfg
        self.team_results: dict[str, deque[int]] = defaultdict(lambda: deque(maxlen=cfg.form_window))
        self.h2h_results: dict[tuple[str, str], deque[int]] = defaultdict(lambda: deque(maxlen=cfg.h2h_window))

    def team_form(self, team: str) -> float:
        d = self.team_results[team]
        return 0.5 if not d else sum(d) / len(d)

    def h2h_form(self, team_a: str, team_b: str) -> float:
        key = tuple(sorted((team_a, team_b)))
        d = self.h2h_results[key]
        if not d:
            return 0.5
        if (team_a, team_b) == key:
            return sum(d) / len(d)
        return 1.0 - (sum(d) / len(d))

    def update(self, team1: str, team2: str, winner: str) -> None:
        t1w = 1 if winner == team1 else 0
        self.team_results[team1].append(t1w)
        self.team_results[team2].append(1 - t1w)
        key = tuple(sorted((team1, team2)))
        self.h2h_results[key].append(t1w if key[0] == team1 else 1 - t1w)
