"""Smoke tests — verify the synthetic→features→score→ingest path doesn't break."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.ingest.base import (
    USDC_BASE,
    decode_x402_signer,
    normalize,
)
from src.ingest.facilitators import ALL_FACILITATORS, facilitator_label
from src.ingest.synthetic import generate
from src.pipeline import run_pipeline


CANONICAL_COLS = {
    "block_number",
    "block_time_s",
    "tx_hash",
    "from_addr",
    "to_addr",
    "value_wei",
    "value_usd",
    "gas_used",
    "gas_price_gwei",
    "method_id",
    "success",
    "is_x402",
    "facilitator",
}


def test_pipeline_runs(tmp_path: Path) -> None:
    paths = run_pipeline(
        out_dir=str(tmp_path),
        hours=2.0,
        n_human=5,
        n_agent_arb=3,
        n_agent_payment=3,
        n_agent_compromised=2,
        n_collusion_rings=1,
    )
    for name, p in paths.items():
        assert p.exists(), f"{name} artifact missing at {p}"
    txs = pd.read_parquet(paths["transactions"])
    assert len(txs) > 0
    assert CANONICAL_COLS.issubset(txs.columns)


def test_synthetic_emits_x402_columns() -> None:
    txs, labels = generate(
        n_human=2, n_agent_arb=2, n_agent_payment=4, n_agent_compromised=2,
        n_collusion_rings=0, duration_hours=4.0, seed=7,
    )
    assert "is_x402" in txs.columns
    assert "facilitator" in txs.columns
    pay_addrs = labels.loc[labels["policy"] == "agent_payment_bot", "addr"].tolist()
    pay_txs = txs[txs["from_addr"].isin(pay_addrs)]
    assert pay_txs["is_x402"].any(), "payment-bot wallets should produce x402 traffic"
    human_addrs = labels.loc[labels["policy"] == "human_random", "addr"].tolist()
    human_txs = txs[txs["from_addr"].isin(human_addrs)]
    if len(human_txs):
        assert not human_txs["is_x402"].any(), "humans should not be tagged x402"


def test_decode_x402_signer_extracts_address() -> None:
    expected_signer = "0x" + "ab" * 20
    selector = "0xe3ee160e"
    from_word = "0" * 24 + "ab" * 20
    to_word = "0" * 64
    value_word = f"{1_000_000:064x}"
    payload = selector + from_word + to_word + value_word
    assert decode_x402_signer(payload) == expected_signer


def test_decode_x402_signer_handles_garbage() -> None:
    assert decode_x402_signer(None) is None
    assert decode_x402_signer("0xdeadbeef") is None
    assert decode_x402_signer("not hex") is None


def test_ingest_uses_signer_not_facilitator() -> None:
    """Critical invariant: from_addr must be the EIP-3009 signer, not tx.from."""
    facilitator_addr = next(iter(ALL_FACILITATORS))
    real_agent = "0x" + "cd" * 20
    selector = "0xe3ee160e"
    from_word = "0" * 24 + "cd" * 20
    to_word = "0" * 24 + "ee" * 20
    value_word = f"{2_500_000:064x}"
    valid_after = "0" * 64
    valid_before = "f" * 64
    nonce = "0" * 64
    input_hex = selector + from_word + to_word + value_word + valid_after + valid_before + nonce

    raw = pd.DataFrame([{
        "blockNumber": 42_000_001,
        "timeStamp": 1_745_000_000,
        "hash": "0x" + "11" * 32,
        "from": facilitator_addr,
        "to": USDC_BASE,
        "value": "0",
        "gasUsed": "60000",
        "gasPrice": "1000000000",
        "input": input_hex,
        "isError": "0",
    }])
    canonical = normalize(raw)
    assert canonical.loc[0, "is_x402"] is True or bool(canonical.loc[0, "is_x402"])
    assert canonical.loc[0, "from_addr"] == real_agent
    assert canonical.loc[0, "facilitator"] == facilitator_label(facilitator_addr)
    assert canonical.loc[0, "value_usd"] == 2.5  # 2_500_000 / 10**6


def test_live_tracker_warmup_clears_and_alerts_fire() -> None:
    """Live tracker must clear warm-up within ~50 ticks on the demo replay
    and produce at least one alert within 200 ticks. Validates the
    architecture-critical claim from the Plan-agent review:
    population-statistic scoring + percentile-based alerts."""
    from src.live.tracker import LiveTracker, MIN_POPULATION, demo_replay

    tracker = LiveTracker(demo_replay("data/processed/real_x402_payments.parquet"))
    warm_at: int | None = None
    alerts = []
    for i in range(220):
        event = tracker.tick()
        if event is None:
            break
        if not event.warming_up and warm_at is None:
            warm_at = i + 1
        if event.alert is not None:
            alerts.append(event.alert)
    assert warm_at is not None and warm_at <= 50, (
        f"warm-up should clear within 50 ticks; got {warm_at}"
    )
    assert tracker.population_size >= MIN_POPULATION
    assert len(alerts) >= 1, "expected at least one alert in 220 ticks"
    # Alerts must include explanation + non-zero score
    for a in alerts:
        assert a["explanation"]
        assert a["composite_score"] > 0
        assert a["tier"] in {"critical", "high", "medium", "low"}


def test_live_tracker_alert_only_on_new_tx_wallet() -> None:
    """Ensure we don't fire alerts on wallets whose buffer didn't change
    this tick (Plan-agent review item)."""
    from src.live.tracker import LiveTracker, demo_replay

    tracker = LiveTracker(demo_replay("data/processed/real_x402_payments.parquet"))
    for _ in range(220):
        event = tracker.tick()
        if event is None:
            break
        if event.alert is not None:
            assert event.alert["wallet"] == str(event.tx["from_addr"]), (
                "alert wallet must match the tx that triggered the tick"
            )


def test_trend_locked_numbers_render() -> None:
    """The trend tab must render even before snapshot parquets exist."""
    from src.viz.trend import load_or_locked, trend_figure_plotly

    agg, is_live = load_or_locked({"early_adopters": Path("/__missing__.parquet")})
    assert is_live is False
    assert len(agg) == 3
    assert {"date_label", "median_tx_usd", "unique_payers"}.issubset(agg.columns)
    fig = trend_figure_plotly(agg)
    assert len(fig.data) == 4  # 4 panels


def test_trend_aggregates_live_snapshots(tmp_path: Path) -> None:
    """When per-snapshot parquets exist (cofounder's pull_dune.py output), aggregate them.

    Schema: block_time, payer, merchant, value_usd. Oct snapshot is excluded from
    the headline trend by EXCLUDED_FROM_TREND.
    """
    from src.viz.trend import aggregate_from_files

    paths = {}
    for label, n, val in [
        ("early_adopters", 10, 0.1),
        ("post_linux_fdn", 89, 108.0),  # excluded
        ("post_stripe", 15, 0.01),
        ("current", 20, 0.001),
    ]:
        df = pd.DataFrame([
            {"block_time": pd.Timestamp("2026-04-24"), "payer": f"0x{i:040x}", "merchant": "0xa" * 40, "value_usd": val}
            for i in range(n)
        ])
        p = tmp_path / f"snap_{label}.parquet"
        df.to_parquet(p, index=False)
        paths[label] = p

    agg = aggregate_from_files(paths)
    assert len(agg) == 3  # Oct excluded
    assert "post_linux_fdn" not in set(agg["snapshot"])
    assert agg.loc[agg["snapshot"] == "current", "tx_count"].iloc[0] == 20

    agg_all = aggregate_from_files(paths, include_excluded=True)
    assert len(agg_all) == 4
    assert "post_linux_fdn" in set(agg_all["snapshot"])


def test_ingest_loads_jsonl(tmp_path: Path) -> None:
    """End-to-end: write a JSONL file, ingest it via the CLI entry."""
    from src.ingest.base import ingest

    path = tmp_path / "raw.jsonl"
    with path.open("w") as f:
        f.write(json.dumps({
            "blockNumber": 42_000_002,
            "timeStamp": 1_745_000_100,
            "hash": "0x" + "22" * 32,
            "from": "0x" + "01" * 20,
            "to": "0x" + "02" * 20,
            "value": "1000000000000000000",
            "gasUsed": "21000",
            "gasPrice": "1000000000",
            "input": "0x",
            "isError": "0",
        }) + "\n")
    out, lp = ingest(path, out_path=tmp_path / "out.parquet")
    txs = pd.read_parquet(out)
    assert len(txs) == 1
    assert CANONICAL_COLS.issubset(txs.columns)
    labels = pd.read_parquet(lp)
    assert {"addr", "is_agent", "is_compromised_weak", "source"}.issubset(labels.columns)
