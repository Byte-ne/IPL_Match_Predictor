from __future__ import annotations
from dataclasses import dataclass
from datetime import date as Date

@dataclass(frozen=True)
class MatchDayContext:
    fixture_id: str
    team1: str
    team2: str
    venue: str
    date: Date
    toss_winner: str = ""
    toss_decision: str = ""
    team1_xi: list[str] | None = None
    team2_xi: list[str] | None = None

@dataclass(frozen=True)
class MatchSummary:
    fixture_id: str
    name: str
    status: str
    venue: str
    date: Date | None
    team1: str
    team2: str
