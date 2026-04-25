# 16 — Snapshot findings (pitch numbers locked)

**Date:** 2026-04-25

## Headline numbers

| Metric | Jun 2025 | Jan 2026 | Apr 2026 | Δ end-to-end |
|---|---|---|---|---|
| Sample size (tx) | 151 (full month) | 351 (1h) | 400 (1h) | — |
| Unique payers | 39 | 42 | 55 | +41% |
| Unique merchants | 29 | 53 | 24 | concentrating |
| Median tx (USD) | $0.10 | $0.01 | $0.001 | **100× compression** |
| Mean tx (USD) | $124 | $4.17 | $1.63 | (right-skewed by whales) |

## Volume scaling

Daily volume estimate: **5 tx/day (Jun 2025) → ~140k tx/day (Apr 2026) — 28,000× growth in 10 months.**

Estimated by extrapolating measured 1h windows × 24, validated against a 7-day Dune query showing
~590k x402 tx total in the last week (~84k/day baseline; April probe at 140k/day reflects April acceleration).

## Bipartite concentration (Apr 2026, 1h window)

- 24 merchants serving 55 unique payers
- 2.3 agents per merchant in any moment — agent traffic is graph-structured around a small set of API providers.

## What this means for fraud detection (pitch core)

Existing fraud models — Visa Decision Intelligence, Mastercard Brighterion, Stripe Radar — train on a human transaction distribution with median $30–$100. A $0.001 transaction is below their feature representation entirely. **Agent traffic isn't anomalous to them — it's invisible.**

The behavioural distribution is also non-stationary: median compressed 100× in 10 months. Quarterly model retraining (Visa's release cycle) cannot keep up with monthly distribution shifts.

## Methodology

Source: Dune Analytics on Base mainnet.
- x402 traffic: `base.transactions` JOIN `erc20_base.evt_Transfer` WHERE `to = USDC AND selector = 0xe3ee160e` (transferWithAuthorization)
- Snapshots: 1h windows at noon UTC on 2025-06-15 (extended to month for low volume), 2026-01-20, 2026-04-24
- Reproducible via `scripts/run_dune.py --use_cache` against `data/raw/dune_results/summary.json`

## Excluded snapshot

2025-10-15 excluded from trend after sanity check — see `17_real_data_quality.md`.
