# 05 — Data plan

**Date:** 2026-04-25

## Primary source: Base L2 + x402

x402 facilitator addresses on Base are public. Coinbase Developer Platform publishes them. Pull recent transactions interacting with these facilitators → agent-positive class. Pull sampled regular EOAs → human-baseline class.

**Volume target:** 100k transactions for the demo. Stablecoin transaction volume hit $33T in 2025 (+72% YoY); agent-driven Layer 2 spikes of 10,000% in early 2026 — should be plenty.

## Cofounder action

Cofounder is pulling Coinbase data. Confirm format: ideally raw transaction rows with `(block_number, block_time, from, to, value, gas_used, gas_price, input_data_or_method_id, success)`. CSV or parquet works; JSONL OK.

If Coinbase access is API-direct: `cdp.coinbase.com/api/v2/networks/base/transactions` style.

## Schema we standardise on

```python
columns = [
    "block_number",   # int
    "block_time",     # datetime UTC
    "tx_hash",        # str
    "from_addr",      # str (lowercased)
    "to_addr",        # str (lowercased; contract or EOA)
    "value_wei",      # int (native ETH)
    "value_usd",      # float (token-aware, post-decode)
    "gas_used",       # int
    "gas_price",      # int (wei)
    "method_id",      # str (4-byte selector hex, or "0x" for native transfer)
    "success",        # bool
    "is_x402",        # bool — interacted with known facilitator
    "facilitator",    # str | None
]
```

Stored as parquet at `data/raw/base_<date>.parquet`.

## Labels

- **Positive (agent):** addresses appearing on x402 facilitator interactions, or known agent-deployer addresses (Coinbase publishes a list).
- **Negative (human):** EOAs in the same time window with no x402 interaction, no contract creation, < 100 tx/day.
- **Unknown:** the rest. Treat as test set.

This is weak supervision. Good enough for the demo.

## Synthetic fallback (always-on)

`src/ingest/synthetic.py` — policy library generating ground-truth-labelled traffic:

| Policy | Behaviour |
|--------|-----------|
| `human_random` | Poisson arrivals (λ=4/day), value lognormal(μ=4, σ=1.5), high counterparty diversity, time-of-day human curve |
| `agent_arb_deterministic` | High-freq cron (every 60–90s), tight gas (within 1 gwei), 2–3 counterparties only, uniform across 24h |
| `agent_payment_bot` | Bursty (10 tx in 30s, then quiet), small fixed value, single counterparty per burst |
| `agent_compromised` | Starts as `agent_payment_bot`, drifts: gas spikes, value spikes, new counterparty after t=8h |
| `collusion_ring` | 5–10 wallets coordinating: trades within 60s of each other, shared counterparties |

Output matches the Base schema above + a sidecar `<run>_labels.parquet` with `(addr, policy, role)`.

## Demo data flow

```
data/synthetic/run1.parquet  (or data/raw/base_*.parquet when ready)
    ↓
src.features.fingerprint
    ↓
data/processed/features.parquet  (per-wallet rows, 30-50 cols)
    ↓
src.models.cluster + src.models.score
    ↓
data/processed/clusters.parquet, scores.parquet
    ↓
src.viz.umap → results/headline_figure.png
```

## Risk: real Base volume thinner than expected

Mitigation: synthetic generator is the primary path; real data layered in if we have time. Saturday's pitch can demo on synthetic with real-data validation as a "and the same pipeline runs on 100k Base transactions" closer.
