"""Public real-data pipeline for no-key x402 sources."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.features.fingerprint import compute_features
from src.ingest.public_x402 import collect
from src.models.score import score_wallets
from src.viz.embed import build_embedding


def run_public_pipeline(out_dir: str = "data", tx_offset: int = 200, refresh: bool = False) -> dict[str, Path]:
    root = Path(out_dir)
    processed = root / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    collected = collect(out_dir=out_dir, tx_offset=tx_offset) if refresh else {}
    real_path = collected.get("real_x402", processed / "real_x402_base.parquet")
    if not real_path.exists():
        collected = collect(out_dir=out_dir, tx_offset=tx_offset)
        real_path = collected["real_x402"]

    real = pd.read_parquet(real_path)
    payments = real[real["is_x402_eip3009"]].copy()
    payments_path = processed / "real_x402_payments.parquet"
    features_path = processed / "real_x402_features.parquet"
    scores_path = processed / "real_x402_scores.parquet"
    embedding_path = processed / "real_x402_embedding.parquet"
    sample_payments_path = processed / "sample_real_x402_payments.csv"
    sample_scores_path = processed / "sample_real_x402_scores.csv"

    payments.to_parquet(payments_path, index=False)
    payments.head(100).to_csv(sample_payments_path, index=False)

    features = compute_features(payments)
    features.to_parquet(features_path)
    scores = score_wallets(features) if len(features) else pd.DataFrame()
    scores.to_parquet(scores_path)
    scores.head(100).to_csv(sample_scores_path)

    embedding = build_embedding(features, labels=None, scores=scores) if len(features) else pd.DataFrame()
    embedding.to_parquet(embedding_path, index=False)

    return {
        "real_x402": real_path,
        "payments": payments_path,
        "features": features_path,
        "scores": scores_path,
        "embedding": embedding_path,
        "sample_payments": sample_payments_path,
        "sample_scores": sample_scores_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out_dir", type=str, default="data")
    parser.add_argument("--tx_offset", type=int, default=200)
    parser.add_argument("--refresh", action="store_true", help="re-fetch public data before cooking")
    args = parser.parse_args()

    paths = run_public_pipeline(out_dir=args.out_dir, tx_offset=args.tx_offset, refresh=args.refresh)
    payments = pd.read_parquet(paths["payments"])
    scores = pd.read_parquet(paths["scores"])
    print("cooked public x402 data:")
    for name, path in paths.items():
        print(f"  {name:16} {path}")
    print()
    print(f"decoded payment rows: {len(payments):,}")
    print(f"payer wallets: {payments['from_addr'].nunique():,}")
    print(f"recipient wallets: {payments['to_addr'].nunique():,}")
    if len(scores):
        print(f"scored payer wallets: {len(scores):,}")
        print(f"tier breakdown: {scores['tier'].value_counts().to_dict()}")
        print("top scored wallets:")
        for addr, row in scores.head(8).iterrows():
            print(f"  {addr[:10]} | {row['composite_score']:5.1f} | {row['tier']:8} | {row['explanation']}")


if __name__ == "__main__":
    main()
