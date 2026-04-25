"""2D embedding for the dashboard headline plot.

UMAP is the preferred projection because it preserves neighbourhood structure
well enough for a demo cluster plot. If UMAP is unavailable, this falls back to
PCA so the pipeline still runs on a bare machine.
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


DROP_COLUMNS = {"policy", "role", "ring_id", "tier", "explanation"}


def _numeric_matrix(features: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    numeric = features.select_dtypes(include=[np.number]).copy()
    numeric = numeric.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    cols = [c for c in numeric.columns if c not in DROP_COLUMNS]
    X = numeric[cols].to_numpy(dtype=float)
    X = StandardScaler().fit_transform(X)
    return X, cols


def build_embedding(
    features: pd.DataFrame,
    labels: pd.DataFrame | None = None,
    scores: pd.DataFrame | None = None,
    random_state: int = 42,
) -> pd.DataFrame:
    """Return per-wallet x/y embedding joined to labels and scores."""
    X, _ = _numeric_matrix(features)
    if len(features) < 3:
        coords = np.zeros((len(features), 2))
        method = "constant"
    else:
        try:
            import umap

            reducer = umap.UMAP(
                n_components=2,
                n_neighbors=min(18, max(2, len(features) - 1)),
                min_dist=0.08,
                metric="euclidean",
                random_state=random_state,
            )
            coords = reducer.fit_transform(X)
            method = "umap"
        except Exception:
            coords = PCA(n_components=2, random_state=random_state).fit_transform(X)
            method = "pca"

    out = pd.DataFrame(coords, index=features.index, columns=["x", "y"])
    out.index.name = "from_addr"
    out["embedding_method"] = method
    out["tx_count"] = features["tx_count"].astype(float)

    if scores is not None and len(scores) > 0:
        out = out.join(scores[["composite_score", "tier", "explanation"]], how="left")
    if labels is not None and len(labels) > 0:
        labels = labels.copy()
        if "addr" in labels.columns:
            labels = labels.set_index("addr")
        out = out.join(labels[["policy", "role", "ring_id"]], how="left")

    defaults: dict[str, str | float] = {
        "policy": "unlabelled",
        "role": "unknown",
        "tier": "unknown",
        "composite_score": 0.0,
        "explanation": "",
    }
    for column, default in defaults.items():
        if column not in out.columns:
            out[column] = default
        else:
            out[column] = out[column].fillna(default)
    return out.reset_index()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("features", type=str)
    parser.add_argument("--labels", type=str, default="data/synthetic/run1_labels.parquet")
    parser.add_argument("--scores", type=str, default="data/processed/scores.parquet")
    parser.add_argument("-o", "--out", type=str, default="data/processed/embedding.parquet")
    args = parser.parse_args()

    features = pd.read_parquet(args.features)
    labels = pd.read_parquet(args.labels) if args.labels else None
    scores = pd.read_parquet(args.scores) if args.scores else None
    embedding = build_embedding(features, labels=labels, scores=scores)
    embedding.to_parquet(args.out, index=False)
    print(f"wrote {len(embedding):,} embedded wallets to {args.out}")
    print(f"method: {embedding['embedding_method'].iloc[0] if len(embedding) else 'none'}")


if __name__ == "__main__":
    main()
