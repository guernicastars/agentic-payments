# 14 — Real data quality notes

**Date:** 2026-04-25 (post-Dune pull)

> **Status: TEMPLATE.** Append observations as they surface during the Saturday integration.

## Oct 2025 outlier

If the Oct 2025 snapshot shows ~89 tx with $108 median vs $0.10 / $0.001 on adjacent points → top-5 merchant share dominates → drop from headline trend, keep in appendix slide.

Working hypothesis: short institutional testing wave following the Linux Foundation x402 announcement. Treat as a known regime break, not a bug.

## Live x402 thinness

If the live (`--strategy live`) pull returns only ~1k rows in a 60-min window: acceptable for the demo. ~17 tx/min averages to ~84k tx/day, consistent with cross-checks against Dune dashboards.

If it returns <200 rows: re-run with `--window_minutes 15 --row_limit_x402 700`. Burns more datapoints but produces a usable cohort.

## Baseline contamination

The non-x402 baseline includes any Base ETH transfer in the window — so it sweeps in MEV bots and other non-x402 automation. Acceptable for the hackathon: it produces a "humans + non-x402 automation" cluster, and the x402 agents still separate distinctly from it.

Production fix: filter baseline against known MEV bot lists (flashbots, mev-inspect) before publishing as a clean human baseline.

## `gas_used` placeholders in snapshots

If snapshot rows ship with `gas_used` constant (e.g. 55000) because the snapshot query selects only successful x402 settlements, then `gas_used_cv` collapses to 0 and the gas-tightness signal is non-discriminative on snapshot data. Documented as a known feature degradation when running the pipeline against snapshot vs live data.

## Schema gaps observed

[Append as discovered.] e.g. missing `block_time` if only block_number returned, missing `success` flag, missing `tx_hash`. `loader._ensure()` backfills with safe defaults but discriminative power suffers.

## Reproducibility caveats

- Dune execution IDs persist ~3 months. After that the `summary.json` is a stale passport and the queries re-execute (~paid).
- `base.transactions` table is updated continuously; identical query re-runs against "latest" produce different counts. For pitch reproducibility, freeze the parquet, not the query.
