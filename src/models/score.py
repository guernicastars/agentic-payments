"""Composite suspicion score per agent wallet (0–100).

Adapted from polymarket/pipeline/jobs/insider_detector.py + signal_compositor.py.

Eight weighted risk factors, each normalised to [0, 100]:
  1. inter_arrival_anomaly       — log_cv departure from population (low CV → cron-bot tail)
  2. tod_uniformity_anomaly      — KS distance from uniform near 0 → high
  3. gas_tightness_anomaly       — gas_to_basefee_std small + gas_used_cv small → high
  4. counterparty_concentration  — top1 share large
  5. method_concentration        — single-selector share large
  6. burst_intensity             — bursts/hour (z over population)
  7. drift_signal                — new_counterparty_late_share (compromise drift)
  8. coordination                — coordination_partner_count z-score

Composite = clamp(Σ w_i · score_i, 0, 100). Weights default to memos/04_polymarket_assets.md.

Tier mapping (from insider_detector):
  ≥75 critical | ≥50 high | ≥25 medium | <25 low

For each flagged wallet, generates a 1-2 sentence interpretability explanation
from the top-3 z-score features (the demo's "why was this flagged" line).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

import numpy as np
import pandas as pd


WEIGHTS: dict[str, float] = {
    "inter_arrival_anomaly":       0.15,
    "tod_uniformity_anomaly":      0.15,
    "gas_tightness_anomaly":       0.20,
    "counterparty_concentration":  0.10,
    "method_concentration":        0.05,
    "burst_intensity":             0.10,
    "drift_signal":                0.10,
    "coordination":                0.15,
}


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return float(max(lo, min(hi, x)))


def _zscore(s: pd.Series) -> pd.Series:
    mu = s.mean()
    sigma = s.std(ddof=0)
    if sigma == 0:
        return s * 0.0
    return (s - mu) / sigma


def _suspicion_tier(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _onesided(z: pd.Series, direction: str = "high") -> pd.Series:
    """Map z-score to [0, 100] using one-sided sigmoid centred at 0.

    direction='high': z > 0 is suspicious. score(0) ≈ 50, score(2) ≈ 95.
    direction='low':  z < 0 is suspicious.
    """
    if direction == "low":
        z = -z
    # shift right by 1.0 sigma so baseline (z≈0) maps near 25, z=1 near 50, z=2 near 75
    score = 100.0 * (1.0 / (1.0 + np.exp(-(z - 1.0) * 1.5)))
    return score.clip(0, 100)


def _baseline_zscore(s: pd.Series, baseline_mask: pd.Series | None = None) -> pd.Series:
    """Z-score against a baseline subset (e.g. low-volume wallets ≈ human proxy).

    If baseline_mask is None, uses the population.
    """
    if baseline_mask is not None and baseline_mask.sum() > 5:
        ref = s[baseline_mask]
    else:
        ref = s
    mu = ref.mean()
    sigma = ref.std(ddof=0)
    if sigma == 0 or np.isnan(sigma):
        return s * 0.0
    return (s - mu) / sigma


def _factor_scores(features: pd.DataFrame) -> pd.DataFrame:
    """Each factor in [0, 100]. Calibrated against a low-volume baseline (proxy
    for human users) so the pathological agent profiles drive scores high while
    the baseline cohort sits near 0."""
    f = features.copy()
    out = pd.DataFrame(index=f.index)
    # Baseline: lowest 30% of tx_count — dominated by humans in real traffic
    baseline_mask = f["tx_count"] <= f["tx_count"].quantile(0.30)

    # 1) inter_arrival_anomaly — either cron (very low CV) OR drift (very high CV)
    # is suspicious. Deviation from baseline median in either direction.
    cv = f["inter_arrival_cv"]
    cv_med = cv[baseline_mask].median() if baseline_mask.sum() > 5 else cv.median()
    cv_mad = (cv[baseline_mask] - cv_med).abs().median() if baseline_mask.sum() > 5 else (cv - cv_med).abs().median()
    cv_mad = max(float(cv_mad), 1e-6)
    cv_dev = (cv - cv_med).abs() / cv_mad
    out["inter_arrival_anomaly"] = _onesided(cv_dev - 1.0, "high")

    # 2) tod_uniformity — low KS = uniform = agent-like.
    out["tod_uniformity_anomaly"] = _onesided(
        _baseline_zscore(f["tod_uniformity_ks"], baseline_mask), "low"
    )

    # 3) gas_tightness — small gas_to_basefee_std AND small gas_used_cv vs baseline
    z_std = _baseline_zscore(f["gas_to_basefee_std"], baseline_mask)
    z_cv = _baseline_zscore(f["gas_used_cv"], baseline_mask)
    out["gas_tightness_anomaly"] = _onesided((z_std + z_cv) / 2, "low")

    # 4) counterparty_concentration — high top1 share, weighted by activity volume
    z_top1 = _baseline_zscore(f["counterparty_top1_share"], baseline_mask)
    z_n = _baseline_zscore(np.log1p(f["tx_count"]), baseline_mask)
    out["counterparty_concentration"] = _onesided((z_top1 + z_n) / 2, "high")

    # 5) method_concentration
    z_m = _baseline_zscore(f["method_top1_share"], baseline_mask)
    out["method_concentration"] = _onesided((z_m + z_n) / 2, "high")

    # 6) burst_intensity
    out["burst_intensity"] = _onesided(
        _baseline_zscore(f["bursts_per_hour"], baseline_mask), "high"
    )

    # 7) drift_signal — late-window new counterparties (compromise drift)
    out["drift_signal"] = _onesided(
        _baseline_zscore(f["new_counterparty_late_share"], baseline_mask), "high"
    )

    # 8) coordination
    out["coordination"] = _onesided(
        _baseline_zscore(f["coordination_partner_count"], baseline_mask), "high"
    )

    return out


def _explain(features: pd.Series, factors: pd.Series, top_k: int = 3) -> str:
    """One-sentence interpretability for a single wallet."""
    top = factors.sort_values(ascending=False).head(top_k)
    fragments = []
    for factor, score in top.items():
        if factor == "gas_tightness_anomaly":
            fragments.append(
                f"gas-to-basefee std {features['gas_to_basefee_std']:.3f} (top-1% tightness)"
            )
        elif factor == "tod_uniformity_anomaly":
            fragments.append(
                f"24h-uniform timing (KS {features['tod_uniformity_ks']:.2f})"
            )
        elif factor == "inter_arrival_anomaly":
            fragments.append(
                f"inter-arrival CV {features['inter_arrival_cv']:.2f} ({'cron' if features['inter_arrival_cv'] < 0.2 else 'bursty'})"
            )
        elif factor == "drift_signal":
            fragments.append(
                f"{features['new_counterparty_late_share']*100:.0f}% of late-window tx to new counterparties"
            )
        elif factor == "coordination":
            fragments.append(
                f"coordinated with {int(features['coordination_partner_count'])} other wallets"
            )
        elif factor == "counterparty_concentration":
            fragments.append(
                f"{features['counterparty_top1_share']*100:.0f}% volume to single counterparty"
            )
        elif factor == "method_concentration":
            fragments.append(
                f"{features['method_top1_share']*100:.0f}% calls to one selector"
            )
        elif factor == "burst_intensity":
            fragments.append(
                f"{features['bursts_per_hour']:.1f} bursts/hour"
            )
    return "; ".join(fragments)


def score_wallets(features: pd.DataFrame, weights: dict[str, float] | None = None) -> pd.DataFrame:
    """Return DataFrame with per-wallet composite score, tier, factor breakdown, and explanation."""
    weights = weights or WEIGHTS
    factors = _factor_scores(features)
    composite = np.zeros(len(features))
    for k, w in weights.items():
        composite = composite + factors[k].to_numpy() * w
    composite = pd.Series(np.clip(composite, 0, 100), index=features.index, name="composite_score")

    tier = composite.apply(_suspicion_tier).rename("tier")
    explanations = []
    for addr in features.index:
        explanations.append(_explain(features.loc[addr], factors.loc[addr]))
    out = pd.concat([composite, tier, factors], axis=1)
    out["explanation"] = explanations
    out = out.sort_values("composite_score", ascending=False)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=str, help="features parquet")
    p.add_argument("-o", "--out", type=str, default="data/processed/scores.parquet")
    args = p.parse_args()
    feats = pd.read_parquet(args.input)
    scored = score_wallets(feats)
    scored.to_parquet(args.out)
    tier_counts = scored["tier"].value_counts().to_dict()
    print(f"scored {len(scored)} wallets → {args.out}")
    print(f"tier breakdown: {tier_counts}")
    print("\ntop 10 most suspicious:")
    for addr, row in scored.head(10).iterrows():
        print(f"  {addr[:10]} | {row['composite_score']:5.1f} | {row['tier']:8} | {row['explanation']}")


if __name__ == "__main__":
    main()
