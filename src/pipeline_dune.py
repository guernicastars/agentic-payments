"""Cook CTO/Dune x402 exports into the behavioural risk pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.features.fingerprint import compute_features
from src.models.score import score_wallets
from src.viz.embed import build_embedding


TRANSFER_WITH_AUTH_SELECTOR = "0xe3ee160e"


RAW_FILES = {
    "traffic": "x402_live_traffic.parquet",
    "baseline": "x402_baseline.parquet",
    "facilitators": "x402_facilitators.parquet",
    "early_adopters": "x402_snapshot_2025_06_early_adopters.parquet",
    "post_linux_fdn": "x402_snapshot_2025_10_post_linux_fdn.parquet",
    "post_stripe": "x402_snapshot_2026_01_post_stripe.parquet",
    "current": "x402_snapshot_2026_04_current.parquet",
}


SNAPSHOT_META = {
    "early_adopters": "2025-06 full month",
    "post_linux_fdn": "2025-10-15 full day",
    "post_stripe": "2026-01-20 12-13 UTC",
    "current": "2026-04-24 12-13 UTC",
}


def _read_raw(raw_dir: Path, key: str) -> pd.DataFrame:
    path = raw_dir / RAW_FILES[key]
    if not path.exists():
        raise FileNotFoundError(f"Missing Dune raw file: {path}")
    return pd.read_parquet(path)


def _seconds_from_window_start(times: pd.Series) -> pd.Series:
    ts = pd.to_datetime(times, utc=True, errors="coerce")
    min_ts = ts.min()
    if pd.isna(min_ts):
        return pd.Series([0.0] * len(times), index=times.index)
    return (ts - min_ts).dt.total_seconds().fillna(0.0)


def normalise_dune_events(raw_dir: Path, eth_usd: float = 3000.0) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return canonical payment events and per-payer weak labels.

    The Dune live table is true x402/EIP-3009 USDC traffic. The baseline table
    is ordinary Base ETH transfers from the same pull window; it gives the
    scorer a rough human/low-automation reference distribution.
    """
    traffic = _read_raw(raw_dir, "traffic").copy()
    baseline = _read_raw(raw_dir, "baseline").copy()

    traffic_out = pd.DataFrame({
        "block_time": pd.to_datetime(traffic["block_time"], utc=True, errors="coerce"),
        "from_addr": traffic["payer"].astype(str).str.lower(),
        "to_addr": traffic["merchant"].astype(str).str.lower(),
        "value_usd": pd.to_numeric(traffic["value_usd"], errors="coerce").fillna(0.0),
        "gas_price_gwei": pd.to_numeric(traffic["gas_price_gwei"], errors="coerce").fillna(0.0),
        "gas_used": pd.to_numeric(traffic["gas_used"], errors="coerce").fillna(0.0),
        "method_id": TRANSFER_WITH_AUTH_SELECTOR,
        "success": True,
        "source": "dune_x402_live",
        "facilitator_addr": traffic.get("facilitator", pd.Series([None] * len(traffic))).astype(str).str.lower(),
    })

    baseline_out = pd.DataFrame({
        "block_time": pd.to_datetime(baseline["block_time"], utc=True, errors="coerce"),
        "from_addr": baseline["payer"].astype(str).str.lower(),
        "to_addr": baseline["merchant"].astype(str).str.lower(),
        "value_usd": pd.to_numeric(baseline["value_eth"], errors="coerce").fillna(0.0) * eth_usd,
        "gas_price_gwei": pd.to_numeric(baseline["gas_price_gwei"], errors="coerce").fillna(0.0),
        "gas_used": pd.to_numeric(baseline["gas_used"], errors="coerce").fillna(0.0),
        "method_id": "0x",
        "success": True,
        "source": "base_baseline",
        "facilitator_addr": "",
    })

    events = pd.concat([traffic_out, baseline_out], ignore_index=True)
    events = events.dropna(subset=["block_time"])
    events = events[
        events["from_addr"].str.startswith("0x", na=False)
        & events["to_addr"].str.startswith("0x", na=False)
    ].sort_values("block_time").reset_index(drop=True)
    events["block_time_s"] = _seconds_from_window_start(events["block_time"])
    events["network"] = "base"
    events["is_x402"] = events["source"].eq("dune_x402_live")
    events["baseline_eth_usd_assumption"] = float(eth_usd)

    x402_payers = set(events.loc[events["is_x402"], "from_addr"])
    label_rows = []
    for addr, group in events.groupby("from_addr", sort=False):
        if addr in x402_payers:
            policy = "dune_x402_payer"
            role = "observed_agent_payment"
        else:
            policy = "base_baseline"
            role = "baseline_reference"
        label_rows.append({
            "addr": addr,
            "policy": policy,
            "role": role,
            "ring_id": "",
            "tx_count": int(len(group)),
        })
    labels = pd.DataFrame(label_rows)
    return events, labels


def build_snapshot_summary(raw_dir: Path) -> pd.DataFrame:
    rows = []
    for key in ["early_adopters", "post_linux_fdn", "post_stripe", "current"]:
        df = _read_raw(raw_dir, key).copy()
        if len(df):
            values = pd.to_numeric(df["value_usd"], errors="coerce").fillna(0.0)
            times = pd.to_datetime(df["block_time"], utc=True, errors="coerce")
            rows.append({
                "snapshot": key,
                "period": SNAPSHOT_META[key],
                "rows": int(len(df)),
                "payers": int(df["payer"].astype(str).str.lower().nunique()),
                "merchants": int(df["merchant"].astype(str).str.lower().nunique()),
                "volume_usd": float(values.sum()),
                "mean_value_usd": float(values.mean()),
                "median_value_usd": float(values.median()),
                "p90_value_usd": float(values.quantile(0.90)),
                "first_block_time": times.min(),
                "last_block_time": times.max(),
            })
        else:
            rows.append({
                "snapshot": key,
                "period": SNAPSHOT_META[key],
                "rows": 0,
                "payers": 0,
                "merchants": 0,
                "volume_usd": 0.0,
                "mean_value_usd": 0.0,
                "median_value_usd": 0.0,
                "p90_value_usd": 0.0,
                "first_block_time": pd.NaT,
                "last_block_time": pd.NaT,
            })
    return pd.DataFrame(rows)


def run_dune_pipeline(
    out_dir: str = "data",
    eth_usd: float = 3000.0,
) -> dict[str, Path]:
    root = Path(out_dir)
    raw_dir = root / "raw"
    processed = root / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    events, labels = normalise_dune_events(raw_dir=raw_dir, eth_usd=eth_usd)
    features = compute_features(events)
    scores = score_wallets(features) if len(features) else pd.DataFrame()
    embedding = build_embedding(features, labels=labels, scores=scores) if len(features) else pd.DataFrame()
    snapshot_summary = build_snapshot_summary(raw_dir=raw_dir)

    paths = {
        "events": processed / "dune_x402_events.parquet",
        "labels": processed / "dune_x402_labels.parquet",
        "features": processed / "dune_x402_features.parquet",
        "scores": processed / "dune_x402_scores.parquet",
        "embedding": processed / "dune_x402_embedding.parquet",
        "snapshot_summary": processed / "dune_x402_snapshot_summary.parquet",
        "sample_events": processed / "sample_dune_x402_events.csv",
        "sample_scores": processed / "sample_dune_x402_scores.csv",
        "sample_snapshot_summary": processed / "sample_dune_x402_snapshot_summary.csv",
    }
    events.to_parquet(paths["events"], index=False)
    labels.to_parquet(paths["labels"], index=False)
    features.to_parquet(paths["features"])
    scores.to_parquet(paths["scores"])
    embedding.to_parquet(paths["embedding"], index=False)
    snapshot_summary.to_parquet(paths["snapshot_summary"], index=False)

    events.head(200).to_csv(paths["sample_events"], index=False)
    scores.head(200).to_csv(paths["sample_scores"])
    snapshot_summary.to_csv(paths["sample_snapshot_summary"], index=False)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out_dir", type=str, default="data")
    parser.add_argument("--eth_usd", type=float, default=3000.0)
    args = parser.parse_args()

    paths = run_dune_pipeline(out_dir=args.out_dir, eth_usd=args.eth_usd)
    events = pd.read_parquet(paths["events"])
    labels = pd.read_parquet(paths["labels"])
    scores = pd.read_parquet(paths["scores"])
    summary = pd.read_parquet(paths["snapshot_summary"])

    print("cooked Dune x402 data:")
    for name, path in paths.items():
        print(f"  {name:24} {path}")
    print()
    print(f"events: {len(events):,} ({int(events['is_x402'].sum()):,} x402 + {int((~events['is_x402']).sum()):,} baseline)")
    print(f"scored actors: {len(scores):,}")
    if len(scores):
        print(f"tier breakdown: {scores['tier'].value_counts().to_dict()}")
        joined = scores.join(labels.set_index("addr")[["policy"]], how="left")
        print("policy x tier:")
        print(pd.crosstab(joined["policy"], joined["tier"]).to_string())
    print()
    print("snapshot summary:")
    print(summary[["snapshot", "rows", "payers", "merchants", "volume_usd", "median_value_usd"]].to_string(index=False))


if __name__ == "__main__":
    main()
