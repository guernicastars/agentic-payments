"""H5/H6: do synthetic policy classes separate in feature space?

Hypotheses
----------
H5 (memo 07): The five synthetic policies (human_random, agent_arb, agent_payment,
  agent_compromised, collusion_ring) produce per-wallet feature vectors that
  cluster by policy. Test: silhouette score in 36-feature space (>0.2 = strong),
  and a stratified train/test 5-class classifier baseline.

H6 (memo 08): At least 60% of the 36 features carry non-trivial discriminative
  power (mutual information against policy label). Test: per-feature MI, plot
  the distribution, count features above MI=0.05.

Output
------
- results/tables/feature_separation.csv  -- silhouette + classifier accuracy + per-class F1
- results/tables/feature_mi.csv           -- MI per feature, sorted
- results/figures/feature_mi.png          -- bar chart
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import mutual_info_classif
from sklearn.metrics import classification_report, silhouette_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

from src.features.fingerprint import compute_features
from src.ingest.synthetic import generate


def build_dataset(seed: int = 17) -> tuple[pd.DataFrame, pd.Series]:
    txs, labels = generate(
        n_human=120, n_agent_arb=50, n_agent_payment=50,
        n_agent_compromised=20, n_collusion_rings=4,
        ring_size_min=5, ring_size_max=8,
        duration_hours=24.0, seed=seed,
    )
    feats = compute_features(txs).fillna(0.0)
    feats = feats[(feats["tx_count"] > 0)]
    labels = labels.set_index("addr").loc[feats.index]
    return feats, labels["policy"]


def silhouette_and_classifier(X: np.ndarray, y: np.ndarray) -> dict:
    Xs = StandardScaler().fit_transform(X)
    sil = silhouette_score(Xs, y, metric="euclidean", random_state=0)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    accs, reports = [], []
    for tr, te in skf.split(Xs, y):
        clf = RandomForestClassifier(n_estimators=200, random_state=0, n_jobs=-1)
        clf.fit(Xs[tr], y[tr])
        accs.append(clf.score(Xs[te], y[te]))
        reports.append(classification_report(y[te], clf.predict(Xs[te]), output_dict=True, zero_division=0))
    macro_f1 = float(np.mean([r["macro avg"]["f1-score"] for r in reports]))
    return {
        "silhouette": float(sil),
        "rf_accuracy_5fold_mean": float(np.mean(accs)),
        "rf_accuracy_5fold_std": float(np.std(accs)),
        "rf_macro_f1_5fold_mean": macro_f1,
    }


def per_feature_mi(X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    mi = mutual_info_classif(X.to_numpy(), y.to_numpy(), random_state=0)
    out = pd.DataFrame({"feature": X.columns, "mutual_information": mi})
    out = out.sort_values("mutual_information", ascending=False).reset_index(drop=True)
    return out


def fig_mi(mi: pd.DataFrame, threshold: float, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    colors = ["#2a9d8f" if v >= threshold else "#c0c5cc" for v in mi["mutual_information"]]
    ax.barh(mi["feature"][::-1], mi["mutual_information"][::-1], color=colors[::-1], edgecolor="white")
    ax.axvline(threshold, color="#264653", linestyle="--", linewidth=1.0, label=f"MI >= {threshold:.2f}")
    ax.set_xlabel("Mutual information vs synthetic policy label (5 classes)")
    ax.set_title("H6: per-feature discriminative power")
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    feats, y = build_dataset()
    print(f"dataset: {len(feats):,} wallets, {feats.shape[1]} features, {y.nunique()} classes")
    print("class counts:")
    print(y.value_counts().to_string())

    print()
    print("=" * 70)
    print("H5: cluster separation by policy in 36-feature space")
    print("=" * 70)
    h5 = silhouette_and_classifier(feats.to_numpy(), y.to_numpy())
    for k, v in h5.items():
        print(f"  {k:34s} {v}")
    h5["verdict"] = (
        "supported" if h5["silhouette"] >= 0.2 and h5["rf_accuracy_5fold_mean"] >= 0.85 else "weak"
    )
    print(f"  {'verdict':34s} {h5['verdict']}")

    print()
    print("=" * 70)
    print("H6: feature discriminative power (mutual information)")
    print("=" * 70)
    mi = per_feature_mi(feats, y)
    threshold = 0.05
    n_useful = int((mi["mutual_information"] >= threshold).sum())
    print(f"features with MI >= {threshold:.2f}: {n_useful} of {len(mi)} ({100*n_useful/len(mi):.0f}%)")
    print("top 10:")
    print(mi.head(10).to_string(index=False))
    h6 = {
        "n_features": len(mi),
        "n_useful_at_005": n_useful,
        "fraction_useful": n_useful / len(mi),
        "median_mi": float(mi["mutual_information"].median()),
        "verdict": "supported" if n_useful / len(mi) >= 0.6 else "weak",
    }

    fig_mi(mi, threshold, Path("results/figures/feature_mi.png"))
    pd.DataFrame([{"hypothesis": "H5_cluster_separation_by_policy", **h5}]).to_csv(
        "results/tables/feature_separation.csv", index=False
    )
    mi.to_csv("results/tables/feature_mi.csv", index=False)

    print()
    print(f"H6 verdict: {h6['verdict']} ({n_useful}/{len(mi)} features at MI >= {threshold})")
    print("\nwrote: results/tables/feature_separation.csv")
    print("       results/tables/feature_mi.csv")
    print("       results/figures/feature_mi.png")


if __name__ == "__main__":
    main()
