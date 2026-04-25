# 15 — CTO Dune data import

**Date:** 2026-04-25

## What arrived

The CTO sent `/Users/meuge/Downloads/dune_data.zip`.

Contents:

- `dune_results/facilitators.csv`
- `dune_results/x402_traffic.csv`
- `dune_results/baseline.csv`
- `dune_results/snapshot_early_adopters.csv`
- `dune_results/snapshot_post_linux_fdn.csv`
- `dune_results/snapshot_post_stripe.csv`
- `dune_results/snapshot_current.csv`
- Dune pull/probe/analyse scripts.

The zip was unpacked locally to `data/raw/dune_cto_20260425/` for inspection. That staging folder is intentionally ignored by git.

## Important finding

The CTO CSVs are **exactly equivalent** to the already committed Dune parquet artifacts on `main`:

| CTO CSV | Tracked parquet |
|---|---|
| `facilitators.csv` | `data/raw/x402_facilitators.parquet` |
| `x402_traffic.csv` | `data/raw/x402_live_traffic.parquet` |
| `baseline.csv` | `data/raw/x402_baseline.parquet` |
| `snapshot_early_adopters.csv` | `data/raw/x402_snapshot_2025_06_early_adopters.parquet` |
| `snapshot_post_linux_fdn.csv` | `data/raw/x402_snapshot_2025_10_post_linux_fdn.parquet` |
| `snapshot_post_stripe.csv` | `data/raw/x402_snapshot_2026_01_post_stripe.parquet` |
| `snapshot_current.csv` | `data/raw/x402_snapshot_2026_04_current.parquet` |

So the durable source of truth should be the tracked parquets, not another copy of the zip.

## Raw Dune pull summary

Live pull:

- `x402_traffic`: 1,021 rows, 2026-04-25 09:41:35 to 10:16:51 UTC.
- `baseline`: 2,000 ordinary Base transfer rows, 2026-04-25 09:44:57 to 10:16:57 UTC.
- `facilitators`: top 20 facilitators by recent x402 tx count.

Snapshot pull:

| Snapshot | Period | Rows | Payers | Merchants | Volume USD | Median USD |
|---|---:|---:|---:|---:|---:|---:|
| early_adopters | 2025-06 full month | 151 | 39 | 29 | 18,728.45 | 0.100 |
| post_linux_fdn | 2025-10-15 full day | 89 | 53 | 5 | 61,043.67 | 108.000 |
| post_stripe | 2026-01-20 12-13 UTC | 351 | 42 | 53 | 1,464.55 | 0.010 |
| current | 2026-04-24 12-13 UTC | 400 | 55 | 24 | 651.26 | 0.001 |

The snapshots are not perfectly comparable windows: June is a full month, October is a full day, January/April are one-hour capped windows. Treat them as story evidence for changing market shape, not clean time-series statistics.

## Cooking done

New pipeline:

```bash
python -m src.pipeline_dune
```

Outputs:

- `data/processed/dune_x402_events.parquet`
- `data/processed/dune_x402_labels.parquet`
- `data/processed/dune_x402_features.parquet`
- `data/processed/dune_x402_scores.parquet`
- `data/processed/dune_x402_embedding.parquet`
- `data/processed/dune_x402_snapshot_summary.parquet`
- `data/processed/sample_dune_x402_events.csv`
- `data/processed/sample_dune_x402_scores.csv`
- `data/processed/sample_dune_x402_snapshot_summary.csv`

The Dune pipeline normalizes:

- x402 rows as `source=dune_x402_live`, `method_id=0xe3ee160e`, `is_x402=true`.
- baseline rows as `source=base_baseline`, `method_id=0x`, `is_x402=false`.

The baseline ETH value is converted to an approximate USD value using `ETH_USD=3000` for feature compatibility. This is not a price claim; it is a pragmatic normalization so baseline rows can pass through the same feature machinery.

## First model readout

Cooked events:

- 3,021 canonical events.
- 1,021 x402 settlement rows.
- 2,000 ordinary Base baseline rows.
- 1,798 scored actors.

Risk tiers:

| Policy | Low | Medium |
|---|---:|---:|
| base_baseline | 1,212 | 217 |
| dune_x402_payer | 314 | 55 |

No high/critical claims should be made from this Dune pull. The value is that we now have:

1. A real x402 traffic panel for the dashboard.
2. A live ordinary-Base baseline for calibration.
3. Snapshot evidence for x402 market evolution.
4. Reproducible Dune scripts for fresh pulls when keys are available.

## Dashboard change

The Streamlit dashboard now has three datasets:

- `Synthetic stress test`
- `Dune x402 + baseline`
- `Public x402 Base`

The Dune tab is the best current bridge between synthetic validation and public real-data overlay.
