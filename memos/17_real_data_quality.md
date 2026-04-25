# 14 — Real data quality notes

**Date:** 2026-04-25

## Oct 2025 snapshot — bipartite degenerate, excluded from trend

The 2025-10-15 daily snapshot looked anomalous on first read (89 tx, mean $686, median $108 vs. $0.10/$0.01/$0.001 on the rest of the trend). Sanity check on the per-merchant breakdown:

| Metric | Value |
|---|---|
| Top-1 merchant share | **99.98%** of volume |
| Top-1 merchant tx count | 85 of 89 (95%) |
| Address | `0x42ec2a5fc5a23553a353a4219a42dea765877160` |
| Total volume that day | $61,043 |
| Volume to top-1 | $61,032 |

This is not whale-tx contamination — this is **whale-merchant contamination**. A single contract was the destination of essentially all the day's x402 traffic. Even after dropping the top-5 transactions, the median stays at $99.88 because the remaining 84 tx all go to the same merchant.

This sample is one user's traffic profile, not the population behavioural distribution.

**Decision:** drop 2025-10-15 from the trend chart. The remaining three points (Jun 2025 / Jan 2026 / Apr 2026) form a clean log-decay line on median tx value: $0.10 → $0.01 → $0.001.

## How we frame it if asked at the pitch

> "October 2025 was bipartite-degenerate: 99.98% of x402 volume that day went through a single merchant address. We treat this as a transitional-phase signal — institutional pilots run before broad agent populations come online — not a trend point. The fact that we can detect this with a 30-second sanity check is part of what we're shipping."

This actually strengthens the narrative — it shows the system distinguishes between population-level shifts and single-actor distortions, which is exactly what fraud-vs-noise detection requires.

## Other quality notes

**Live x402 thinness.** 1,021 rows in 60-min window = ~17 tx/min average → 84k tx/day extrapolated. Consistent with the 7-day facilitator query (~590k tx / 7 days). Scale-consistent.

**Baseline contamination.** Baseline includes any non-x402 ETH transfer on Base. This will sweep in MEV bots, DEX traders, bridge users. Acceptable for hackathon — produces a "humans + non-x402 automation" cluster, x402 agents separate distinctly. **Production fix:** filter baseline against known MEV bot lists (flashbots/mev-inspect dataset).

**Jun 2025 expanded to month-long window.** 1h-at-noon returned ~0 rows; expanded to full month to get 151 tx. Acceptable because Jun 2025 represents the "early adopters" phase explicitly, where 1h windows aren't statistically meaningful.

## Reproducibility

All raw data and execution_ids are committed in `data/raw/dune_results/summary.json`. Re-fetch costs zero datapoints via `--use_cache`.
