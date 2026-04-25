"""Pre-compute every artefact needed by the Next.js port and dump as JSON.

Outputs:
  web/public/data/events.json     -- one record per LiveTracker tick
                                     (tx, population_size, warming_up,
                                      score / tier on the source wallet,
                                      alert payload if fired)
  web/public/data/trend.json      -- per-snapshot aggregates for the
                                     12-month trend chart
  web/public/data/scores.json     -- final live-population score table
                                     (top 25, for the leaderboard)
  web/public/data/embedding.json  -- pre-computed UMAP coords for the
                                     behaviour-map scatter
  web/public/data/meta.json       -- counts + build timestamp

Run from repo root:  python scripts/export_to_web.py
"""

from __future__ import annotations

import json
import math
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from src.live.tracker import LiveTracker, demo_replay
from src.viz.trend import LOCKED_NUMBERS, aggregate_from_files


warnings.filterwarnings("ignore", category=RuntimeWarning)


REPLAY_PARQUET = Path("data/processed/real_x402_payments.parquet")
OUT_DIR = Path("web/public/data")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _safe_float(v) -> float | None:
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def export_events(max_ticks: int = 360) -> int:
    tracker = LiveTracker(demo_replay(REPLAY_PARQUET))
    events: list[dict] = []
    for tick_no in range(1, max_ticks + 1):
        e = tracker.tick()
        if e is None:
            break
        wallet = str(e.tx.get("from_addr", ""))
        wallet_score = None
        wallet_tier = None
        if len(e.scores) and wallet in e.scores.index:
            wallet_score = _safe_float(e.scores.loc[wallet, "composite_score"])
            wallet_tier = str(e.scores.loc[wallet, "tier"])
        events.append({
            "tick": tick_no,
            "tx": {
                "from_addr": wallet,
                "to_addr": str(e.tx.get("to_addr", "")),
                "value_usd": _safe_float(e.tx.get("value_usd")) or 0.0,
                "tx_hash": str(e.tx.get("tx_hash", "")),
                "block_time_s": _safe_float(e.tx.get("block_time_s")) or 0.0,
                "method_id": str(e.tx.get("method_id", "")),
            },
            "population_size": int(e.population_size),
            "warming_up": bool(e.warming_up),
            "score": wallet_score,
            "tier": wallet_tier,
            "alert": e.alert if e.alert else None,
        })
    OUT_DIR.joinpath("events.json").write_text(json.dumps(events))
    return len(events)


def export_trend() -> int:
    try:
        agg = aggregate_from_files(include_excluded=True)
        if len(agg) == 0:
            agg = LOCKED_NUMBERS.copy()
            agg["volume_usd"] = (agg["mean_tx_usd"] * agg["tx_count"]).round(2)
            source = "locked_numbers"
        else:
            source = "live_snapshots"
    except Exception:
        agg = LOCKED_NUMBERS.copy()
        agg["volume_usd"] = (agg["mean_tx_usd"] * agg["tx_count"]).round(2)
        source = "locked_numbers"
    rows = [{k: (None if pd.isna(v) else (float(v) if isinstance(v, (int, float, np.integer, np.floating)) else str(v)))
             for k, v in r.items()}
            for r in agg.to_dict(orient="records")]
    OUT_DIR.joinpath("trend.json").write_text(json.dumps({"source": source, "rows": rows}))
    return len(rows)


def export_scores_and_embedding() -> tuple[int, int]:
    """Run the full LiveTracker stream once, dump final scores + 2D embedding.

    Pre-projection uses PCA (cheap, deterministic). UMAP would be nicer but
    drags in numba; PCA is good enough for the pitch scatter.
    """
    tracker = LiveTracker(demo_replay(REPLAY_PARQUET))
    last_scores: pd.DataFrame | None = None
    last_event = None
    while True:
        e = tracker.tick()
        if e is None:
            break
        if len(e.scores):
            last_scores = e.scores
        last_event = e

    if last_scores is None or len(last_scores) == 0:
        OUT_DIR.joinpath("scores.json").write_text(json.dumps([]))
        OUT_DIR.joinpath("embedding.json").write_text(json.dumps([]))
        return 0, 0

    scored = last_scores.reset_index().rename(columns={"index": "wallet"})
    if "wallet" not in scored.columns:
        scored.rename(columns={"from_addr": "wallet"}, inplace=True)
    if "wallet" not in scored.columns:
        scored["wallet"] = scored.iloc[:, 0]
    scored = scored.sort_values("composite_score", ascending=False).reset_index(drop=True)

    # Top 25 leaderboard
    top = scored.head(25).copy()
    leaderboard = []
    for _, r in top.iterrows():
        wallet = str(r["wallet"])
        leaderboard.append({
            "wallet": wallet,
            "wallet_short": wallet[:10] + "...",
            "score": _safe_float(r.get("composite_score")) or 0.0,
            "tier": str(r.get("tier", "low")),
            "explanation": str(r.get("explanation", "")),
        })
    OUT_DIR.joinpath("scores.json").write_text(json.dumps(leaderboard))

    # 2D embedding via PCA over factor columns
    factor_cols = [
        "inter_arrival_anomaly", "tod_uniformity_anomaly", "gas_tightness_anomaly",
        "counterparty_concentration", "method_concentration", "burst_intensity",
        "drift_signal", "coordination",
    ]
    avail = [c for c in factor_cols if c in scored.columns]
    n_emb = 0
    if len(avail) >= 2 and len(scored) >= 3:
        X = scored[avail].fillna(0.0).to_numpy()
        # Standardise
        X = (X - X.mean(0)) / (X.std(0) + 1e-9)
        pcs = PCA(n_components=2, random_state=0).fit_transform(X)
        emb_rows = []
        for i, (_, r) in enumerate(scored.iterrows()):
            wallet = str(r["wallet"])
            emb_rows.append({
                "wallet": wallet,
                "wallet_short": wallet[:10] + "...",
                "x": float(pcs[i, 0]),
                "y": float(pcs[i, 1]),
                "score": _safe_float(r.get("composite_score")) or 0.0,
                "tier": str(r.get("tier", "low")),
            })
        OUT_DIR.joinpath("embedding.json").write_text(json.dumps(emb_rows))
        n_emb = len(emb_rows)
    else:
        OUT_DIR.joinpath("embedding.json").write_text(json.dumps([]))

    return len(leaderboard), n_emb


def export_meta(events_n: int, trend_n: int, scores_n: int, emb_n: int) -> None:
    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "events": events_n,
        "trend_rows": trend_n,
        "scores_rows": scores_n,
        "embedding_rows": emb_n,
        "headline": {
            "median_compression": 100,
            "volume_growth": 28000,
            "rf_accuracy": 99.6,
            "feature_mi_pass_rate": 97,
        },
    }
    OUT_DIR.joinpath("meta.json").write_text(json.dumps(meta, indent=2))


def main() -> None:
    events_n = export_events()
    trend_n = export_trend()
    scores_n, emb_n = export_scores_and_embedding()
    export_meta(events_n, trend_n, scores_n, emb_n)
    print(f"events:    {events_n:5d} -> web/public/data/events.json")
    print(f"trend:     {trend_n:5d} -> web/public/data/trend.json")
    print(f"scores:    {scores_n:5d} -> web/public/data/scores.json")
    print(f"embedding: {emb_n:5d} -> web/public/data/embedding.json")


if __name__ == "__main__":
    main()
