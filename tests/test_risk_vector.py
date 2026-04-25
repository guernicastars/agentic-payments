"""Tests for the six-dimension risk vector and tracker warm-up invariants."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.ingest.synthetic import generate
from src.features.fingerprint import compute_features
from src.models.score import (
    FACTOR_KEYS,
    SUBSCORE_KEYS,
    SUBSCORE_WEIGHTS,
    score_wallets,
)
from src.live.tracker import LiveTracker, ReplayStream, MIN_POPULATION, MIN_WALLET_TX


# --------------------------------------------------------------------------- #
# score_wallets output schema                                                   #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def scored_df() -> pd.DataFrame:
    txs, _ = generate(
        n_human=10,
        n_agent_arb=5,
        n_agent_payment=5,
        n_agent_compromised=3,
        n_collusion_rings=1,
        duration_hours=4.0,
    )
    features = compute_features(txs).fillna(0.0)
    return score_wallets(features)


def test_score_wallets_has_six_subscores(scored_df: pd.DataFrame) -> None:
    for col in SUBSCORE_KEYS:
        assert col in scored_df.columns, f"missing subscore column: {col}"


def test_score_wallets_has_legacy_composite(scored_df: pd.DataFrame) -> None:
    assert "composite_score" in scored_df.columns
    assert "overall_action_risk" in scored_df.columns
    pd.testing.assert_series_equal(
        scored_df["composite_score"],
        scored_df["overall_action_risk"],
        check_names=False,
    )


def test_subscores_bounded(scored_df: pd.DataFrame) -> None:
    for col in SUBSCORE_KEYS:
        assert scored_df[col].between(0, 100).all(), f"{col} out of [0, 100]"


def test_overall_bounded(scored_df: pd.DataFrame) -> None:
    assert scored_df["overall_action_risk"].between(0, 100).all()


def test_tier_values(scored_df: pd.DataFrame) -> None:
    valid_tiers = {"critical", "high", "medium", "low"}
    assert scored_df["tier"].isin(valid_tiers).all()


def test_weights_sum_to_one() -> None:
    total = sum(SUBSCORE_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9, f"weights sum to {total}, not 1.0"


def test_subscore_keys_match_weights() -> None:
    assert set(SUBSCORE_KEYS) == set(SUBSCORE_WEIGHTS.keys())


def test_factor_keys_present(scored_df: pd.DataFrame) -> None:
    for col in FACTOR_KEYS:
        assert col in scored_df.columns, f"missing factor column: {col}"


def test_top_factors_schema(scored_df: pd.DataFrame) -> None:
    assert "top_factors" in scored_df.columns
    for wallet, row in scored_df.iterrows():
        tf = row["top_factors"]
        assert isinstance(tf, list), f"{wallet}: top_factors must be a list"
        assert 1 <= len(tf) <= 3
        for entry in tf:
            assert "name" in entry and "score" in entry


def test_explanation_is_nonempty_string(scored_df: pd.DataFrame) -> None:
    assert "explanation" in scored_df.columns
    assert scored_df["explanation"].str.len().gt(0).all()


def test_sorted_descending_by_overall(scored_df: pd.DataFrame) -> None:
    vals = scored_df["overall_action_risk"].tolist()
    assert vals == sorted(vals, reverse=True)


def test_prompt_injection_score_zero_without_flag(scored_df: pd.DataFrame) -> None:
    """Real data paths never set prompt_injection_flag, so scores must be 0."""
    assert (scored_df["prompt_injection_score"] == 0).all()


# --------------------------------------------------------------------------- #
# LiveTracker warm-up gate                                                     #
# --------------------------------------------------------------------------- #

class _ListStream:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = iter(rows)

    def __iter__(self):
        return self._rows


def _make_tx(wallet: str, t: float = 0.0) -> dict:
    return {
        "from_addr": wallet,
        "to_addr": "0xdeadbeef",
        "value_usd": 1.0,
        "value_wei": int(1e15),
        "gas_used": 21000,
        "gas_price_gwei": 1.0,
        "block_time_s": t,
        "block_number": int(t),
        "tx_hash": f"0x{hash((wallet, t)) & 0xFFFFFFFFFFFFFFFF:016x}",
        "method_id": "0xa9059cbb",
        "success": True,
        "is_x402": True,
        "facilitator": "facilitator_a",
    }


def test_tracker_warming_up_below_min_population() -> None:
    """No alert should fire until MIN_POPULATION wallets have been seen."""
    rows = [_make_tx(f"0x{i:040x}", float(i)) for i in range(MIN_POPULATION - 1)]
    tracker = LiveTracker(_ListStream(rows))
    events = []
    while True:
        ev = tracker.tick()
        if ev is None:
            break
        events.append(ev)

    assert all(ev.warming_up for ev in events), "tracker should warm up until MIN_POPULATION"
    assert tracker.alerts == [], "no alerts should fire during warm-up"


def test_tracker_population_grows_monotonically() -> None:
    wallets = [f"0x{i:040x}" for i in range(10)]
    rows = [_make_tx(w, float(t)) for t, w in enumerate(wallets)]
    tracker = LiveTracker(_ListStream(rows))
    sizes = []
    while True:
        ev = tracker.tick()
        if ev is None:
            break
        sizes.append(ev.population_size)
    assert sizes == list(range(1, len(wallets) + 1))


def test_tracker_reset_clears_state() -> None:
    rows = [_make_tx(f"0x{i:040x}", float(i)) for i in range(5)]
    tracker = LiveTracker(_ListStream(rows))
    for _ in range(5):
        tracker.tick()
    tracker.reset(_ListStream(rows))
    assert tracker.population_size == 0
    assert tracker.alerts == []
    assert tracker.total_tx_seen == 0
