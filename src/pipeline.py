"""End-to-end synthetic demo pipeline.

Builds the artifacts consumed by the Streamlit demo:
transactions -> wallet features -> coordination clusters -> suspicion scores
-> 2D embedding.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.features.fingerprint import compute_features
from src.ingest.synthetic import generate
from src.models.cluster import cluster_wallets, clusters_to_df
from src.models.score import score_wallets
from src.viz.embed import build_embedding


def _downstream(
    txs: pd.DataFrame,
    labels: pd.DataFrame,
    processed_dir: Path,
) -> dict[str, Path]:
    processed_dir.mkdir(parents=True, exist_ok=True)
    feature_path = processed_dir / "features.parquet"
    cluster_path = processed_dir / "clusters.parquet"
    edge_path = processed_dir / "cluster_edges.parquet"
    score_path = processed_dir / "scores.parquet"
    embedding_path = processed_dir / "embedding.parquet"

    features = compute_features(txs)
    features.to_parquet(feature_path)

    clusters, edges = cluster_wallets(txs)
    clusters_to_df(clusters).to_parquet(cluster_path)
    if len(edges) > 0:
        edges.to_parquet(edge_path, index=False)
    else:
        pd.DataFrame().to_parquet(edge_path, index=False)

    scores = score_wallets(features)
    scores.to_parquet(score_path)

    embedding = build_embedding(features, labels=labels, scores=scores)
    embedding.to_parquet(embedding_path, index=False)
    return {
        "features": feature_path,
        "clusters": cluster_path,
        "cluster_edges": edge_path,
        "scores": score_path,
        "embedding": embedding_path,
    }


def run_pipeline(
    out_dir: str = "data",
    hours: float = 24.0,
    seed: int = 42,
    n_human: int = 100,
    n_agent_arb: int = 40,
    n_agent_payment: int = 40,
    n_agent_compromised: int = 10,
    n_collusion_rings: int = 2,
) -> dict[str, Path]:
    root = Path(out_dir)
    synthetic_dir = root / "synthetic"
    processed_dir = root / "processed"
    synthetic_dir.mkdir(parents=True, exist_ok=True)

    tx_path = synthetic_dir / "run1.parquet"
    label_path = synthetic_dir / "run1_labels.parquet"

    txs, labels = generate(
        n_human=n_human,
        n_agent_arb=n_agent_arb,
        n_agent_payment=n_agent_payment,
        n_agent_compromised=n_agent_compromised,
        n_collusion_rings=n_collusion_rings,
        duration_hours=hours,
        seed=seed,
    )
    txs.to_parquet(tx_path, index=False)
    labels.to_parquet(label_path, index=False)

    artefacts = _downstream(txs, labels, processed_dir)
    return {"transactions": tx_path, "labels": label_path, **artefacts}


def run_pipeline_from_parquet(
    tx_path: str | Path,
    label_path: str | Path | None = None,
    processed_dir: str | Path = "data/processed_base",
) -> dict[str, Path]:
    """Run the downstream feature/score/embed pipeline on an already-ingested
    transaction parquet (e.g. from src.ingest.base).
    """
    tx_path = Path(tx_path)
    txs = pd.read_parquet(tx_path)
    labels = (
        pd.read_parquet(label_path)
        if label_path and Path(label_path).exists()
        else pd.DataFrame(columns=["addr", "policy", "role", "ring_id"])
    )
    if "policy" not in labels.columns and "is_agent" in labels.columns:
        labels = labels.assign(
            policy=labels["is_agent"].map({True: "agent_payment_bot", False: "human_random"}),
            role=labels["is_agent"].map({True: "agent", False: "human"}),
            ring_id=-1,
        )
    artefacts = _downstream(txs, labels, Path(processed_dir))
    return {"transactions": tx_path, "labels": Path(label_path) if label_path else tx_path, **artefacts}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out_dir", type=str, default="data")
    parser.add_argument("--hours", type=float, default=24.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n_human", type=int, default=100)
    parser.add_argument("--n_agent_arb", type=int, default=40)
    parser.add_argument("--n_agent_payment", type=int, default=40)
    parser.add_argument("--n_agent_compromised", type=int, default=10)
    parser.add_argument("--n_collusion_rings", type=int, default=2)
    args = parser.parse_args()

    paths = run_pipeline(**vars(args))
    print("built demo artifacts:")
    for name, path in paths.items():
        print(f"  {name:14} {path}")


if __name__ == "__main__":
    main()
