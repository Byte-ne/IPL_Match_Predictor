from __future__ import annotations
import json, time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class CacheConfig:
    ttl_seconds: int = 6 * 60 * 60

def cache_get_json(cache_dir: Path, key: str, cfg: CacheConfig) -> Any | None:
    p = cache_dir / f"{''.join(c if c.isalnum() or c in '-_' else '_' for c in key)}.json"
    if not p.exists():
        return None
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
        if time.time() - float(payload.get("_cached_at", 0)) > cfg.ttl_seconds:
            return None
        return payload.get("data")
    except Exception:
        return None

def cache_put_json(cache_dir: Path, key: str, data: Any) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    p = cache_dir / f"{''.join(c if c.isalnum() or c in '-_' else '_' for c in key)}.json"
    p.write_text(json.dumps({"_cached_at": time.time(), "data": data}), encoding="utf-8")
