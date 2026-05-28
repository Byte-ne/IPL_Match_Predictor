from __future__ import annotations
from datetime import date as Date
from typing import Any
import requests
from ..config import Paths, env
from .cache import CacheConfig, cache_get_json, cache_put_json
from .types import MatchDayContext, MatchSummary

def _base():
    return (env("CRICAPI_BASE_URL") or "https://api.cricapi.com/v1").rstrip("/")

def _get(paths, endpoint, params, key):
    api_key = env("CRICAPI_KEY")
    if not api_key:
        raise RuntimeError('Set CRICAPI_KEY (see BEGINNER_SETUP.md)')
    cached = cache_get_json(paths.api_cache_dir, key, CacheConfig())
    if cached is not None:
        return cached
    r = requests.get(f"{_base()}/{endpoint}", params={"apikey": api_key, **params}, timeout=30)
    r.raise_for_status()
    data = r.json()
    cache_put_json(paths.api_cache_dir, key, data)
    return data

def _first(d, keys, default=""):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default

def _date(v):
    try:
        return Date.fromisoformat(str(v)[:10])
    except Exception:
        return None

def list_fixtures(paths: Paths, offset=0, ipl_only=True) -> list[MatchSummary]:
    raw = _get(paths, "currentMatches", {"offset": offset}, f"current_{offset}")
    items = raw.get("data") or []
    out = []
    for item in items:
        if not isinstance(item, dict):
            continue
        blob = " ".join(str(item.get(k, "")) for k in ("name", "series", "matchType")).lower()
        if ipl_only and "ipl" not in blob and "indian premier" not in blob:
            continue
        fid = str(_first(item, ["id", "matchId"], ""))
        if not fid:
            continue
        out.append(MatchSummary(fid, str(_first(item, ["name"], "")), str(_first(item, ["status"], "")), str(_first(item, ["venue"], "")), _date(_first(item, ["date", "dateTimeGMT"], "")), str(_first(item, ["team1"], "")), str(_first(item, ["team2"], ""))))
    return out

def fetch_matchday_context(paths: Paths, fixture_id: str) -> MatchDayContext | None:
    api_key = env("CRICAPI_KEY")
    if not api_key:
        return None
    key = f"match_info_{fixture_id}"
    cached = cache_get_json(paths.api_cache_dir, key, CacheConfig())
    if cached is None:
        r = requests.get(f"{_base()}/match_info", params={"apikey": api_key, "id": fixture_id}, timeout=30)
        r.raise_for_status()
        cached = r.json()
        cache_put_json(paths.api_cache_dir, key, cached)
    payload = cached.get("data") if isinstance(cached, dict) else None
    if not isinstance(payload, dict):
        return None
    t1, t2 = _first(payload, ["team1"]), _first(payload, ["team2"])
    v = _first(payload, ["venue"])
    dt = _date(_first(payload, ["date", "dateTimeGMT"]))
    if not (t1 and t2 and v and dt):
        return None
    return MatchDayContext(fixture_id, str(t1), str(t2), str(v), dt, str(_first(payload, ["tossWinner", "toss_winner"], "")), str(_first(payload, ["toss_decision", "tossDecision"], "")).lower())
