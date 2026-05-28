from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    project_root: Path
    data_dir: Path
    raw_dir: Path
    processed_dir: Path
    artifacts_dir: Path
    api_cache_dir: Path


def get_paths(project_root: Path | None = None) -> Paths:
    if project_root is None:
        env_root = os.getenv("IPL_PROJECT_ROOT")
        project_root = Path(env_root) if env_root else Path(__file__).resolve().parents[1]
    else:
        project_root = Path(project_root)
    data_dir = project_root / "data"
    return Paths(
        project_root=project_root,
        data_dir=data_dir,
        raw_dir=data_dir / "raw",
        processed_dir=data_dir / "processed",
        artifacts_dir=project_root / "artifacts",
        api_cache_dir=data_dir / "api_cache",
    )


def env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value
