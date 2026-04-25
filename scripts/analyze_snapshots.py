"""Trend table across the 4 x402 snapshots in data/raw/."""
from pathlib import Path
from statistics import mean, median

import pandas as pd

DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

LABELS = [
    ("x402_snapshot_2025_06_early_adopters.parquet", "early_adopters", "2025-06 (full month)"),
    ("x402_snapshot_2025_10_post_linux_fdn.parquet", "post_linux_fdn", "2025-10-15 (full day)"),
    ("x402_snapshot_2026_01_post_stripe.parquet",    "post_stripe",    "2026-01-20 12-13 UTC"),
    ("x402_snapshot_2026_04_current.parquet",        "current",        "2026-04-24 12-13 UTC"),
]

print(f"{'snapshot':<18} {'period':<24} {'rows':>5} {'payers':>7} {'merch':>6}"
      f" {'vol_usd':>10} {'mean_$':>8} {'median_$':>9} {'p90_$':>8}")
print("-" * 110)

for filename, label, period in LABELS:
    path = DIR / filename
    if not path.exists():
        continue
    df = pd.read_parquet(path)
    if df.empty:
        print(f"{label:<18} {period:<24} {0:>5}")
        continue
    payers = df["payer"].str.lower().nunique()
    merchants = df["merchant"].str.lower().nunique()
    vals = sorted(df["value_usd"].astype(float).tolist())
    total = sum(vals)
    p90 = vals[int(len(vals) * 0.9)] if vals else 0
    print(f"{label:<18} {period:<24} {len(df):>5} {payers:>7}"
          f" {merchants:>6} {total:>10.2f} {mean(vals):>8.4f}"
          f" {median(vals):>9.4f} {p90:>8.4f}")

print("\n--- growth ratios (current vs early_adopters) ---")
def stats(filename):
    p = DIR / filename
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    if df.empty:
        return None
    return {
        "rows": len(df),
        "payers": df["payer"].str.lower().nunique(),
        "merchants": df["merchant"].str.lower().nunique(),
        "mean_val": float(df["value_usd"].mean()),
        "median_val": float(df["value_usd"].median()),
    }

early = stats("x402_snapshot_2025_06_early_adopters.parquet")
curr = stats("x402_snapshot_2026_04_current.parquet")
if early and curr:
    print(f"  rows:        {early['rows']} -> {curr['rows']}  ({curr['rows']/early['rows']:.1f}x)")
    print(f"  payers:      {early['payers']} -> {curr['payers']}  ({curr['payers']/early['payers']:.1f}x)")
    print(f"  merchants:   {early['merchants']} -> {curr['merchants']}  ({curr['merchants']/early['merchants']:.1f}x)")
    print(f"  mean tx $:   {early['mean_val']:.4f} -> {curr['mean_val']:.4f}  ({curr['mean_val']/early['mean_val']:.2f}x)")
    print(f"  median tx $: {early['median_val']:.4f} -> {curr['median_val']:.4f}  ({curr['median_val']/early['median_val']:.2f}x)")
