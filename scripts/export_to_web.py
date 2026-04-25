"""Pre-compute every artefact the Vercel port needs and dump as JSON.

For each demo scenario we emit a separate pre-rolled LiveTracker stream so
the web app is a pure replay. Scenarios:

  base_x402              -- recorded public x402 settlements (real Base
                            data); the production-honest demo
  compromised_drift      -- synthetic, agent_compromised dominates so the
                            pitch shows drift-led alerts
  collusion_ring         -- synthetic, multiple coordinated wallets so the
                            pitch shows coordination-led alerts
  prompt_injected_invoice -- synthetic, the prompt-injected scenario;
                            the most agentic-specific story

Outputs:
  web/public/data/scenarios/<key>/events.json
  web/public/data/scenarios/<key>/scores.json
  web/public/data/scenarios/<key>/embedding.json
  web/public/data/trend.json                  (snapshot trend, scenario-agnostic)
  web/public/data/meta.json                   (build timestamp + scenario list +
                                               headline numbers)

Run from repo root:  python scripts/export_to_web.py
"""

from __future__ import annotations

import json
import math
import shutil
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from src.features.fingerprint import compute_features
from src.ingest.synthetic import generate
from src.live.tracker import (
    SUBSCORE_KEYS,
    LiveTracker,
    ReplayStream,
    demo_replay,
)
from src.models.score import score_wallets
from src.viz.trend import LOCKED_NUMBERS, aggregate_from_files


warnings.filterwarnings("ignore", category=RuntimeWarning)


REPLAY_PARQUET = Path("data/processed/real_x402_payments.parquet")
OUT_DIR = Path("web/public/data")


@dataclass
class Scenario:
    key: str
    label: str
    description: str
    builder: Callable[[], pd.DataFrame]
    max_ticks: int = 360


def _safe_float(v) -> float | None:
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


# -------- scenario builders ------------------------------------------------

def build_base_x402() -> pd.DataFrame:
    """Real Base x402 settlements, hand-curated for fast warm-up.

    Used by the existing `demo_replay` -> ReplayStream pipeline directly;
    we just return the underlying DataFrame so the per-scenario stream
    construction below is uniform.
    """
    return demo_replay(REPLAY_PARQUET)._df  # noqa: SLF001 — internal but OK here


def _round_robin_sort(df: pd.DataFrame, top_n_for_phase1: int = 20) -> pd.DataFrame:
    df = df.sort_values("block_time_s", kind="stable").reset_index(drop=True)
    if len(df) == 0:
        return df
    groups = {a: g.copy() for a, g in df.groupby("from_addr", sort=False)}
    wallet_order = df["from_addr"].value_counts().index.tolist()
    opening_idx = [groups[a].index[0] for a in wallet_order[:top_n_for_phase1]]
    opening_df = df.loc[opening_idx]
    tail = df[~df.index.isin(opening_idx)].copy()
    return pd.concat([opening_df, tail], ignore_index=True)


def build_compromised_drift() -> pd.DataFrame:
    """Synthetic — many compromised agents drift mid-window, plus baseline payment-bots.
    Population sized > MIN_POPULATION so warm-up clears."""
    txs, _ = generate(
        n_human=35, n_agent_arb=15, n_agent_payment=18,
        n_agent_compromised=20, n_prompt_injected=0, n_collusion_rings=0,
        duration_hours=18.0, seed=11,
    )
    return _round_robin_sort(txs)


def build_collusion_ring() -> pd.DataFrame:
    """Synthetic — multiple rings coordinating bursts in a denser population."""
    txs, _ = generate(
        n_human=35, n_agent_arb=12, n_agent_payment=12,
        n_agent_compromised=4, n_prompt_injected=0, n_collusion_rings=4,
        ring_size_min=6, ring_size_max=9,
        duration_hours=14.0, seed=13,
    )
    return _round_robin_sort(txs)


def build_prompt_injected_invoice() -> pd.DataFrame:
    """Synthetic — a wave of prompt-injected agents diverts payments."""
    txs, _ = generate(
        n_human=30, n_agent_arb=12, n_agent_payment=14,
        n_agent_compromised=3, n_prompt_injected=14, n_collusion_rings=0,
        duration_hours=12.0, seed=17,
    )
    return _round_robin_sort(txs)


SCENARIOS: list[Scenario] = [
    Scenario(
        key="base_x402",
        label="Public x402 (Base)",
        description=(
            "Recorded x402 EIP-3009 settlements pulled from Base via "
            "Blockscout. The honest demo: real wallets, real flow, "
            "scoring computed live."
        ),
        builder=build_base_x402,
    ),
    Scenario(
        key="compromised_drift",
        label="Compromised agent (drift)",
        description=(
            "Synthetic — agents start as well-behaved x402 payment bots "
            "and drift to a new counterparty + value pattern after t=8h. "
            "The classic 'compromised credential' fraud shape."
        ),
        builder=build_compromised_drift,
    ),
    Scenario(
        key="collusion_ring",
        label="Collusion ring",
        description=(
            "Synthetic — three coordinated rings of 6-8 wallets each "
            "fire bursts within 60s windows on shared counterparties."
        ),
        builder=build_collusion_ring,
    ),
    Scenario(
        key="prompt_injected_invoice",
        label="Prompt-injected invoice",
        description=(
            "Synthetic — agent reads a tampered invoice mid-window and "
            "diverts payments to an attacker wallet. The agentic-"
            "specific failure mode: action / intent mismatch."
        ),
        builder=build_prompt_injected_invoice,
    ),
]


# -------- exporters --------------------------------------------------------

def _events_for_scenario(s: Scenario) -> list[dict]:
    df = s.builder()
    stream = ReplayStream.__new__(ReplayStream)
    stream._df = df.reset_index(drop=True)  # type: ignore[attr-defined]
    stream._cursor = 0  # type: ignore[attr-defined]
    tracker = LiveTracker(stream)
    events: list[dict] = []
    for tick_no in range(1, s.max_ticks + 1):
        e = tracker.tick()
        if e is None:
            break
        wallet = str(e.tx.get("from_addr", ""))
        scores = e.scores
        wallet_score = None
        wallet_tier = None
        sub: dict[str, float | None] = {k: None for k in SUBSCORE_KEYS}
        if len(scores) and wallet in scores.index:
            wallet_score = _safe_float(scores.loc[wallet, "overall_action_risk"])
            wallet_tier = str(scores.loc[wallet, "tier"])
            for k in SUBSCORE_KEYS:
                if k in scores.columns:
                    sub[k] = _safe_float(scores.loc[wallet, k])
        events.append({
            "tick": tick_no,
            "tx": {
                "from_addr": wallet,
                "to_addr": str(e.tx.get("to_addr", "")),
                "value_usd": _safe_float(e.tx.get("value_usd")) or 0.0,
                "tx_hash": str(e.tx.get("tx_hash", "")),
                "block_time_s": _safe_float(e.tx.get("block_time_s")) or 0.0,
                "method_id": str(e.tx.get("method_id", "")),
                "prompt_injection_flag": bool(e.tx.get("prompt_injection_flag", False)),
            },
            "population_size": int(e.population_size),
            "warming_up": bool(e.warming_up),
            "score": wallet_score,
            "tier": wallet_tier,
            "subscores": sub,
            "alert": e.alert if e.alert else None,
        })
    # Final scores for this scenario (for leaderboard + embedding pages)
    final_scores = pd.DataFrame()
    flat: list[dict] = []
    for buf in tracker._buffers.values():  # type: ignore[attr-defined]
        flat.extend(buf)
    if flat:
        feats = compute_features(pd.DataFrame(flat)).fillna(0.0)
        if len(feats):
            final_scores = score_wallets(feats)
    return events, final_scores


def _leaderboard(scored: pd.DataFrame) -> list[dict]:
    if len(scored) == 0:
        return []
    scored = scored.reset_index().rename(columns={"index": "wallet"})
    if "wallet" not in scored.columns:
        scored.rename(columns={"from_addr": "wallet"}, inplace=True)
    scored = scored.sort_values("overall_action_risk", ascending=False).reset_index(drop=True)
    rows = []
    for _, r in scored.head(25).iterrows():
        wallet = str(r["wallet"])
        rows.append({
            "wallet": wallet,
            "wallet_short": wallet[:10] + "...",
            "score": _safe_float(r.get("overall_action_risk")) or 0.0,
            "tier": str(r.get("tier", "low")),
            "subscores": {k: _safe_float(r.get(k)) or 0.0 for k in SUBSCORE_KEYS if k in r.index},
            "explanation": str(r.get("explanation", "")),
        })
    return rows


def _embedding(scored: pd.DataFrame) -> list[dict]:
    """2D PCA over the six sub-scores. Cheap, deterministic, no numba."""
    if len(scored) < 3:
        return []
    cols = [k for k in SUBSCORE_KEYS if k in scored.columns]
    if len(cols) < 2:
        return []
    X = scored[cols].fillna(0.0).to_numpy()
    # Standardise; if a column is zero (e.g. prompt_injection_score on real
    # data) the std handling already returns 0/(1e-9)->0 column, fine.
    mu = X.mean(0)
    sigma = X.std(0)
    sigma[sigma == 0] = 1.0
    Xs = (X - mu) / sigma
    pcs = PCA(n_components=2, random_state=0).fit_transform(Xs)
    out = []
    for i, (addr, r) in enumerate(scored.iterrows()):
        wallet = str(addr)
        out.append({
            "wallet": wallet,
            "wallet_short": wallet[:10] + "...",
            "x": float(pcs[i, 0]),
            "y": float(pcs[i, 1]),
            "score": _safe_float(r.get("overall_action_risk")) or 0.0,
            "tier": str(r.get("tier", "low")),
        })
    return out


def export_trend() -> int:
    try:
        agg = aggregate_from_files(include_excluded=True)
        source = "live_snapshots" if len(agg) else "locked_numbers"
        if len(agg) == 0:
            agg = LOCKED_NUMBERS.copy()
            agg["volume_usd"] = (agg["mean_tx_usd"] * agg["tx_count"]).round(2)
    except Exception:
        agg = LOCKED_NUMBERS.copy()
        agg["volume_usd"] = (agg["mean_tx_usd"] * agg["tx_count"]).round(2)
        source = "locked_numbers"
    rows = [
        {k: (None if pd.isna(v) else (float(v) if isinstance(v, (int, float, np.integer, np.floating)) else str(v)))
         for k, v in r.items()}
        for r in agg.to_dict(orient="records")
    ]
    OUT_DIR.joinpath("trend.json").write_text(json.dumps({"source": source, "rows": rows}))
    return len(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scenarios_dir = OUT_DIR / "scenarios"
    if scenarios_dir.exists():
        shutil.rmtree(scenarios_dir)
    scenarios_dir.mkdir(parents=True)

    scenario_meta = []
    for s in SCENARIOS:
        sdir = scenarios_dir / s.key
        sdir.mkdir(parents=True, exist_ok=True)
        events, scored = _events_for_scenario(s)
        sdir.joinpath("events.json").write_text(json.dumps(events))
        leaderboard = _leaderboard(scored)
        sdir.joinpath("scores.json").write_text(json.dumps(leaderboard))
        embedding = _embedding(scored)
        sdir.joinpath("embedding.json").write_text(json.dumps(embedding))
        n_alerts = sum(1 for e in events if e.get("alert"))
        scenario_meta.append({
            "key": s.key,
            "label": s.label,
            "description": s.description,
            "events": len(events),
            "alerts": n_alerts,
            "leaderboard_rows": len(leaderboard),
            "embedding_rows": len(embedding),
        })
        print(f"{s.key:30s} events={len(events):4d}  alerts={n_alerts:3d}  scored_wallets={len(scored)}")

    trend_n = export_trend()

    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "trend_rows": trend_n,
        "scenarios": scenario_meta,
        "headline": {
            "median_compression": 100,
            "volume_growth": 28000,
            "rf_accuracy": 99.6,
            "feature_mi_pass_rate": 97,
        },
    }
    OUT_DIR.joinpath("meta.json").write_text(json.dumps(meta, indent=2))
    print(f"\ntrend rows: {trend_n}")
    print(f"wrote {len(SCENARIOS)} scenarios -> web/public/data/scenarios/")


if __name__ == "__main__":
    main()
