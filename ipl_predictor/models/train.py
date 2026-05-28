from __future__ import annotations
from pathlib import Path
from typing import Any
import pandas as pd
from catboost import CatBoostClassifier, Pool
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss
from ..config import Paths
from ..data.download import download_default_dataset, read_dataset_meta
from ..data.schema import load_and_normalize_matches_csv
from ..data.split import time_split_by_season
from ..features.pipeline import build_features_and_state
from .serialize import dump_joblib, dump_json
try:
    from sklearn.frozen import FrozenEstimator
    _HAS_FROZEN = True
except ImportError:
    _HAS_FROZEN = False

def _train_catboost(train_df, valid_df, feature_cols, cat_cols, train_dir):
    cat_idx = [feature_cols.index(c) for c in cat_cols]
    base = CatBoostClassifier(loss_function="Logloss", depth=6, learning_rate=0.06, iterations=1200, random_seed=42, verbose=False, train_dir=str(train_dir) if train_dir else None)
    base.fit(Pool(train_df[feature_cols], train_df["y_team1_win"].astype(int), cat_features=cat_idx), eval_set=Pool(valid_df[feature_cols], valid_df["y_team1_win"].astype(int), cat_features=cat_idx), use_best_model=True)
    cal = CalibratedClassifierCV(FrozenEstimator(base), method="sigmoid") if _HAS_FROZEN else CalibratedClassifierCV(base, method="sigmoid", cv="prefit")
    cal.fit(valid_df[feature_cols], valid_df["y_team1_win"].astype(int))
    return cal

def _evaluate(model, df, feature_cols):
    p = model.predict_proba(df[feature_cols])[:, 1]
    y = df["y_team1_win"].astype(int).to_numpy()
    return {"log_loss": float(log_loss(y, p)), "brier": float(brier_score_loss(y, p)), "accuracy": float(accuracy_score(y, (p >= 0.5).astype(int))), "n": float(len(y))}

def train_mode(mode: str, paths: Paths, raw_csv: Path | None = None) -> dict[str, Any]:
    use_md = mode.lower() in {"matchday", "md"}
    raw_csv = raw_csv or download_default_dataset(paths.raw_dir, force=False)
    feats, state = build_features_and_state(load_and_normalize_matches_csv(raw_csv), use_md)
    split = time_split_by_season(feats, 2)
    feature_cols = ["season", "team1", "team2", "venue", "city", "elo_team1", "elo_team2", "elo_diff", "form_team1", "form_team2", "form_diff", "h2h_team1_vs_team2"]
    cat_cols = ["team1", "team2", "venue", "city"]
    if use_md:
        feature_cols += ["toss_winner", "toss_decision"]
        cat_cols += ["toss_winner", "toss_decision"]
    mode_dir = "matchday" if use_md else "pre"
    out = paths.artifacts_dir / mode_dir
    log = paths.artifacts_dir / "catboost_logs" / mode_dir
    log.mkdir(parents=True, exist_ok=True)
    model = _train_catboost(split.train, split.valid, feature_cols, cat_cols, log)
    metrics = {"train": _evaluate(model, split.train, feature_cols), "valid": _evaluate(model, split.valid, feature_cols)}
    dump_joblib({"model": model, "feature_cols": feature_cols, "cat_cols": cat_cols, "state": state}, out / "model.joblib")
    dump_json(metrics, out / "metrics.json")
    dump_json({"dataset": read_dataset_meta(paths.raw_dir), "state_summary": {"last_season": state.last_season, "teams": len(state.elo_ratings)}}, out / "training_info.json")
    return {"mode": mode_dir, "artifacts_dir": str(out), "metrics": metrics}
