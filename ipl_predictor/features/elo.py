from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class EloConfig:
    base_rating: float = 1500.0
    k: float = 24.0

def expected_score(r_a: float, r_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((r_b - r_a) / 400.0))

def update_elo(r_a: float, r_b: float, score_a: float, k: float) -> tuple[float, float]:
    e_a = expected_score(r_a, r_b)
    d = k * (score_a - e_a)
    return r_a + d, r_b - d
