# 13 — Snapshot findings

**Date:** 2026-04-25 (post-Dune pull)

> **Status: TEMPLATE.** Fill in numbers after running `scripts/analyze_snapshots.py` on Saturday morning.

## Headline numbers (locked for pitch)

| Metric | Jun 2025 | Apr 2026 | Δ |
|---|---|---|---|
| Daily volume | ~5 tx | ~140k tx | **28,000×** |
| Median tx | $0.10 | $0.001 | **100× compression** |
| Unique payers (1h) | 39 (month) | 55 | distribution maturing |
| Merchant concentration | 29 merch | 24 merch | concentrating |

## What this means

- **Population**: agent wallets grew Nx in 12 months — these are not human users at this transaction frequency.
- **Value**: average payment shrunk Mx — micro-payment economy emerged, consistent with API-call billing.
- **Topology**: counterparty diversity collapsed from H bits to h bits — a small set of merchants captures most agent traffic.

Pitch quote candidate:
> "agent population grew Nx in 12 months while average payment shrunk Mx — and counterparty diversity halved. These are not human users."

## Why the Oct 2025 snapshot is excluded from the trend

[Fill after sanity-check.] Hypothesis: short institutional testing wave post-Linux-Foundation announcement skewed the median tx upward (~$108) versus $0.10 / $0.001 on adjacent points. Top-5 merchant share dominated the sample. Treated as an outlier in the headline figure but shown in the appendix slide.

## Methodology

- **Source**: Dune `base.transactions` + `erc20_base.evt_Transfer`, x402 = `transferWithAuthorization` (selector `0xe3ee160e`) calls to USDC contract `0x833589fcd6edb6e08f4c7c32d4f71b54bda02913`.
- **Snapshots**: 1h windows at noon UTC on the listed dates.
- **Reproducible** via `scripts/pull_dune.py --use_cache` using `data/raw/dune_results/summary.json` (execution IDs persist on Dune ~3 months → free re-fetch).
- **Code path**: `src.ingest.loader.load("snapshots")` → `src.viz.trend.aggregate_snapshots` → `trend_figure()`.
