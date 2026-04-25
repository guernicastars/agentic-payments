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
