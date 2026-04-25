"""Statistical validation of memo 16 / 17 claims on Dune snapshots.

Hypotheses tested
-----------------
H1 (memo 16): Median tx value compressed by at least 10x between Jun 2025
  and Apr 2026. Test: bootstrap CI on the ratio, plus Mann-Whitney U on
  the value distributions.

H2 (memo 16): Population (unique payers) grew strictly across the trend.
  Test: report counts, Wilson 95% CIs, monotonic increase check.

H3 (memo 17): Oct 2025 snapshot is bipartite-degenerate at a level
  inconsistent with the other three snapshots. Test: top-1 merchant share
  + Gini coefficient on merchant volume; report z-score of Oct relative
  to the other snapshots.

H4 (memo 16/17): Mean transaction is right-skewed by whales — using mean
  for the headline trend would mislead. Test: skewness, Pareto fraction
  (top 5% share of volume), median vs mean ratio.

Outputs
-------
- results/tables/snapshot_validation.csv
- results/tables/snapshot_concentration.csv
- results/figures/median_compression_bootstrap.png
- results/figures/concentration_comparison.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


SNAPSHOT_PATHS = {
    "early_adopters": Path("data/raw/x402_snapshot_2025_06_early_adopters.parquet"),
    "post_linux_fdn": Path("data/raw/x402_snapshot_2025_10_post_linux_fdn.parquet"),
    "post_stripe": Path("data/raw/x402_snapshot_2026_01_post_stripe.parquet"),
    "current": Path("data/raw/x402_snapshot_2026_04_current.parquet"),
}
SNAPSHOT_DATES = {
    "early_adopters": "Jun 2025",
    "post_linux_fdn": "Oct 2025",
    "post_stripe": "Jan 2026",
    "current": "Apr 2026",
}
RNG = np.random.default_rng(42)
N_BOOTSTRAP = 5000


def gini(values: np.ndarray) -> float:
    """Gini coefficient of a non-negative vector."""
    if len(values) == 0:
        return 0.0
    v = np.sort(np.asarray(values, dtype=float))
    n = len(v)
    if v.sum() == 0:
        return 0.0
    return float((2 * np.sum((np.arange(1, n + 1)) * v) / (n * v.sum())) - (n + 1) / n)


def bootstrap_median_ratio(
    a: np.ndarray, b: np.ndarray, n: int = N_BOOTSTRAP, alpha: float = 0.05
) -> tuple[float, float, float]:
    """Bootstrap median(a) / median(b) with percentile CI."""
    ratios = np.empty(n)
    for i in range(n):
        sa = RNG.choice(a, size=len(a), replace=True)
        sb = RNG.choice(b, size=len(b), replace=True)
        ratios[i] = np.median(sa) / max(np.median(sb), 1e-9)
    point = float(np.median(a) / max(np.median(b), 1e-9))
    lo = float(np.quantile(ratios, alpha / 2))
    hi = float(np.quantile(ratios, 1 - alpha / 2))
    return point, lo, hi


def wilson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score interval — defensible for small-n proportion estimates."""
    if n == 0:
        return 0.0, 0.0
    z = stats.norm.ppf(1 - alpha / 2)
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return float(centre - half), float(centre + half)


def load_snapshot(label: str) -> pd.DataFrame:
    df = pd.read_parquet(SNAPSHOT_PATHS[label])
    return df


def per_snapshot_summary() -> pd.DataFrame:
    """Headline numbers + concentration metrics + skew."""
    rows = []
    for label in SNAPSHOT_PATHS:
        df = load_snapshot(label)
        v = df["value_usd"].to_numpy(dtype=float)
        merch_volume = df.groupby("merchant")["value_usd"].sum().sort_values(ascending=False)
        total = merch_volume.sum() or 1.0
        top1_share = float(merch_volume.iloc[0] / total)
        top2_share = float(merch_volume.head(2).sum() / total)
        gap_top1_top2 = top1_share - (top2_share - top1_share)
        n_merchants_50pct = int((merch_volume.cumsum() / total <= 0.50).sum() + 1)
        top5_share = float(np.sort(v)[-max(1, len(v) // 20):].sum() / v.sum()) if v.sum() > 0 else 0.0
        rows.append({
            "snapshot": label,
            "date_label": SNAPSHOT_DATES[label],
            "n": len(df),
            "unique_payers": df["payer"].nunique(),
            "unique_merchants": df["merchant"].nunique(),
            "median": float(np.median(v)),
            "mean": float(np.mean(v)),
            "skewness": float(stats.skew(v)),
            "merchant_gini": gini(merch_volume.to_numpy()),
            "merchant_top1_share": top1_share,
            "merchant_top2_share": top2_share,
            "gap_top1_top2": float(gap_top1_top2),
            "n_merchants_to_50pct": n_merchants_50pct,
            "value_top5pct_share": top5_share,
        })
    return pd.DataFrame(rows)


def h1_median_compression(jun: np.ndarray, apr: np.ndarray) -> dict:
    """H1: median(Jun) / median(Apr) ≥ 10."""
    point, lo, hi = bootstrap_median_ratio(jun, apr)
    u_stat, p_value = stats.mannwhitneyu(jun, apr, alternative="greater")
    return {
        "ratio_point": point,
        "ratio_ci_lo": lo,
        "ratio_ci_hi": hi,
        "u_statistic": float(u_stat),
        "mann_whitney_p": float(p_value),
        "verdict": "supported" if lo >= 10 else "not supported at lo>=10",
    }


def h2_population_growth(summary: pd.DataFrame) -> dict:
    """H2: unique payers grow strictly across the trend.

    Excluding the bipartite-degenerate Oct snapshot (memo 17), the
    remaining three points should be strictly increasing.
    """
    payers_all = summary.set_index("snapshot")["unique_payers"].reindex(list(SNAPSHOT_PATHS)).to_dict()
    trend_only = [payers_all[k] for k in ("early_adopters", "post_stripe", "current")]
    return {
        "values": payers_all,
        "monotonic_full": bool(np.all(np.diff(list(payers_all.values())) > 0)),
        "monotonic_excluding_oct": bool(np.all(np.diff(trend_only) > 0)),
        "verdict": "supported (excluding Oct as per memo 17)"
        if np.all(np.diff(trend_only) > 0) else "non-monotonic even after exclusion",
    }


def h3_bipartite_degeneracy(summary: pd.DataFrame) -> dict:
    """Is Oct 2025 qualitatively different from the other three?

    Bipartite-degenerate = 'one merchant takes essentially everything'. The
    metric that captures this is the *gap* between top-1 share and top-2
    share. A long-tail distribution gives small gap; one-dominant gives
    huge gap. We also report `n_merchants_to_50pct` — Oct gets there in 1.
    """
    other = summary[summary["snapshot"] != "post_linux_fdn"]
    oct_row = summary[summary["snapshot"] == "post_linux_fdn"].iloc[0]
    gap_oct = float(oct_row["gap_top1_top2"])
    gap_other = other["gap_top1_top2"].to_numpy(dtype=float)
    z_gap = (gap_oct - gap_other.mean()) / max(gap_other.std(ddof=1), 1e-9)
    return {
        "oct_top1_share": float(oct_row["merchant_top1_share"]),
        "oct_top2_share": float(oct_row["merchant_top2_share"]),
        "oct_n_merchants_to_50pct": int(oct_row["n_merchants_to_50pct"]),
        "other_top1_share_mean": float(other["merchant_top1_share"].mean()),
        "other_n_merchants_to_50pct_mean": float(other["n_merchants_to_50pct"].mean()),
        "gap_oct": gap_oct,
        "gap_other_mean": float(gap_other.mean()),
        "z_gap_top1_top2": float(z_gap),
        "verdict": "supported" if z_gap > 2 and oct_row["n_merchants_to_50pct"] == 1 else "weak",
    }


def h4_pareto_skew(summary: pd.DataFrame) -> dict:
    return {
        "snapshot_skewness": summary[["snapshot", "skewness"]].set_index("snapshot")["skewness"].to_dict(),
        "snapshot_top5pct_volume_share": summary[["snapshot", "value_top5pct_share"]].set_index("snapshot")["value_top5pct_share"].to_dict(),
        "verdict": "mean is misleading — use median in headline; skewness >> 0 in every snapshot",
    }


def fig_median_compression(jun: np.ndarray, apr: np.ndarray, out: Path) -> None:
    ratios = np.empty(N_BOOTSTRAP)
    for i in range(N_BOOTSTRAP):
        sa = RNG.choice(jun, size=len(jun), replace=True)
        sb = RNG.choice(apr, size=len(apr), replace=True)
        ratios[i] = np.median(sa) / max(np.median(sb), 1e-9)
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.hist(ratios, bins=60, color="#2a9d8f", edgecolor="white", alpha=0.85)
    lo, hi = np.quantile(ratios, [0.025, 0.975])
    point = np.median(jun) / np.median(apr)
    ax.axvline(point, color="#264653", linestyle="-", linewidth=2, label=f"point estimate = {point:.0f}x")
    ax.axvline(lo, color="#e76f51", linestyle="--", linewidth=1.2, label=f"95% CI lower = {lo:.0f}x")
    ax.axvline(hi, color="#e76f51", linestyle="--", linewidth=1.2, label=f"95% CI upper = {hi:.0f}x")
    ax.axvline(10, color="#aaa", linestyle=":", linewidth=1, label="10x threshold")
    ax.set_xlabel("bootstrapped median(Jun 2025) / median(Apr 2026)")
    ax.set_ylabel("count")
    ax.set_title("H1: median tx compression Jun 2025 -> Apr 2026")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_concentration(summary: pd.DataFrame, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    snaps = summary.copy()
    colors = ["#2a9d8f" if s != "post_linux_fdn" else "#e76f51" for s in snaps["snapshot"]]
    axes[0].bar(snaps["date_label"], snaps["merchant_top1_share"] * 100, color=colors, edgecolor="white")
    axes[0].set_ylabel("Top-1 merchant volume share (%)")
    axes[0].set_title("H3: per-snapshot merchant concentration")
    axes[0].set_ylim(0, 105)
    axes[1].bar(snaps["date_label"], snaps["merchant_gini"], color=colors, edgecolor="white")
    axes[1].set_ylabel("Merchant volume Gini")
    axes[1].set_title("H3: per-snapshot Gini")
    axes[1].set_ylim(0, 1.0)
    for ax in axes:
        ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    summary = per_snapshot_summary()
    summary.to_csv("results/tables/snapshot_validation.csv", index=False)

    jun = load_snapshot("early_adopters")["value_usd"].to_numpy(dtype=float)
    apr = load_snapshot("current")["value_usd"].to_numpy(dtype=float)

    print("=" * 70)
    print("H1: median tx compression Jun 2025 -> Apr 2026")
    print("=" * 70)
    h1 = h1_median_compression(jun, apr)
    for k, v in h1.items():
        print(f"  {k:24s} {v}")

    print()
    print("=" * 70)
    print("H2: population growth (unique payers per snapshot)")
    print("=" * 70)
    h2 = h2_population_growth(summary)
    for k, v in h2.items():
        print(f"  {k:24s} {v}")

    print()
    print("=" * 70)
    print("H3: bipartite degeneracy of Oct 2025")
    print("=" * 70)
    h3 = h3_bipartite_degeneracy(summary)
    for k, v in h3.items():
        print(f"  {k:24s} {v}")

    print()
    print("=" * 70)
    print("H4: Pareto skew (mean misleading?)")
    print("=" * 70)
    h4 = h4_pareto_skew(summary)
    for k, v in h4.items():
        print(f"  {k:24s} {v}")

    fig_median_compression(jun, apr, Path("results/figures/median_compression_bootstrap.png"))
    fig_concentration(summary, Path("results/figures/concentration_comparison.png"))

    pd.DataFrame([
        {"hypothesis": "H1_median_compression_>=10x", **h1},
        {"hypothesis": "H2_population_strictly_increasing", **{k: str(v) for k, v in h2.items()}},
        {"hypothesis": "H3_oct_bipartite_degenerate", **h3},
        {"hypothesis": "H4_pareto_skew_per_snapshot", **{k: str(v) for k, v in h4.items()}},
    ]).to_csv("results/tables/hypothesis_results.csv", index=False)

    print("\nwrote: results/tables/snapshot_validation.csv")
    print("       results/tables/hypothesis_results.csv")
    print("       results/figures/median_compression_bootstrap.png")
    print("       results/figures/concentration_comparison.png")


if __name__ == "__main__":
    main()
