from __future__ import annotations
import hashlib
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class XiHasherConfig:
    dims: int = 32
    salt: str = "ipl_xi_v1"

def parse_xi(xi: str | None) -> list[str]:
    if not xi:
        return []
    return [p.strip() for p in xi.split(",") if p.strip()]

def xi_hash_vector(players: list[str], cfg: XiHasherConfig) -> np.ndarray:
    v = np.zeros(cfg.dims, dtype=np.float32)
    for p in players:
        h = hashlib.md5((cfg.salt + "::" + p.lower()).encode()).hexdigest()
        v[int(h[:8], 16) % cfg.dims] += 1.0
    return v

def xi_diff_features(team1_xi: str | None, team2_xi: str | None, cfg: XiHasherConfig) -> dict[str, float]:
    v1 = xi_hash_vector(parse_xi(team1_xi), cfg)
    v2 = xi_hash_vector(parse_xi(team2_xi), cfg)
    return {f"xi_hash_diff_{i}": float(x) for i, x in enumerate((v1 - v2).tolist())}
