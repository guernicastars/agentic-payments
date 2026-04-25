"""Risk vector per wallet — runtime risk control for autonomous payments.

Six sub-scores in [0, 100], plus an overall_action_risk that drives the tier.

  agent_likeness_score      — is the actor machine-shaped?
                              (timing uniformity, gas optimisation, method concentration)
  drift_score               — has its behaviour changed within the window?
                              (late-window new counterparties, burst intensity)
  coordination_score        — does it move in sync with other wallets?
                              (per-tx neighbour count within 60s)
  policy_violation_score    — is the action outside delegated authority?
                              (large_value_share + late new counterparty proxy)
  counterparty_risk_score   — is the recipient suspicious?
                              (top-1 counterparty concentration + tx-volume z-score)
  prompt_injection_score    — did external content manipulate the action?
                              (driven by a tx-level metadata flag — 0 in
                               real-data ingest paths until the product layer
                               that scores this lands; non-zero only for
                               synthetic prompt-injected scenarios)

Overall action risk = clamp(Σ w_i · sub_i, 0, 100). Tier from the overall risk:
  ≥75 critical | ≥50 high | ≥25 medium | <25 low.

Each row also carries a structured `top_factors` list (top 3 sub-scores with
their values) and a `explanation` string. The legacy `composite_score`
column is kept as an alias for `overall_action_risk` for backward
compatibility with existing exporters and the Streamlit dashboard.

Adapted from polymarket/pipeline/jobs/insider_detector.py and
signal_compositor.py; the eight underlying factor signals are still computed
and exposed for the explanation generator.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

import numpy as np
import pandas as pd


# Eight underlying factor signals (legacy — kept for explanations and back-compat).
FACTOR_KEYS = [
    "inter_arrival_anomaly",
    "tod_uniformity_anomaly",
    "gas_tightness_anomaly",
    "counterparty_concentration",
    "method_concentration",
    "burst_intensity",
    "drift_signal",
    "coordination",
]


# Six product-facing sub-scores.
SUBSCORE_KEYS = [
    "agent_likeness_score",
    "drift_score",
    "coordination_score",
    "policy_violation_score",
    "counterparty_risk_score",
    "prompt_injection_score",
]


# Sub-score weights. Sum to 1. Skewed toward the dimensions a buyer of a
# runtime risk-control product cares about: policy violation and drift /
# prompt injection drive the alert, not raw "agent-likeness" (legitimate
# automation looks agent-like by design).
SUBSCORE_WEIGHTS: dict[str, float] = {
    "agent_likeness_score":     0.10,
    "drift_score":              0.25,
    "coordination_score":       0.15,
    "policy_violation_score":   0.25,
    "counterparty_risk_score":  0.10,
    "prompt_injection_score":   0.15,
}


SUBSCORE_LABEL: dict[str, str] = {
    "agent_likeness_score":     "Agent-likeness",
    "drift_score":              "Behavioural drift",
    "coordination_score":       "Peer coordination",
    "policy_violation_score":   "Policy violation",
    "counterparty_risk_score":  "Counterparty risk",
    "prompt_injection_score":   "Prompt-injection",
}


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return float(max(lo, min(hi, x)))


def _suspicion_tier(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _onesided(z: pd.Series, direction: str = "high") -> pd.Series:
    """Map z-score to [0, 100] using one-sided sigmoid."""
    if direction == "low":
        z = -z
    score = 100.0 * (1.0 / (1.0 + np.exp(-(z - 1.0) * 1.5)))
    return score.clip(0, 100)


def _baseline_zscore(s: pd.Series, baseline_mask: pd.Series | None = None) -> pd.Series:
    """Z-score against a baseline subset (e.g. low-volume wallets ≈ human proxy)."""
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
    """Eight underlying [0, 100] factor signals over a population."""
    f = features.copy()
    out = pd.DataFrame(index=f.index)
    baseline_mask = f["tx_count"] <= f["tx_count"].quantile(0.30)

    cv = f["inter_arrival_cv"]
    cv_med = cv[baseline_mask].median() if baseline_mask.sum() > 5 else cv.median()
    cv_mad = (cv[baseline_mask] - cv_med).abs().median() if baseline_mask.sum() > 5 else (cv - cv_med).abs().median()
    cv_mad = max(float(cv_mad), 1e-6)
    cv_dev = (cv - cv_med).abs() / cv_mad
    out["inter_arrival_anomaly"] = _onesided(cv_dev - 1.0, "high")

    out["tod_uniformity_anomaly"] = _onesided(
        _baseline_zscore(f["tod_uniformity_ks"], baseline_mask), "low"
    )

    z_std = _baseline_zscore(f["gas_to_basefee_std"], baseline_mask)
    z_cv = _baseline_zscore(f["gas_used_cv"], baseline_mask)
    out["gas_tightness_anomaly"] = _onesided((z_std + z_cv) / 2, "low")

    z_top1 = _baseline_zscore(f["counterparty_top1_share"], baseline_mask)
    z_n = _baseline_zscore(np.log1p(f["tx_count"]), baseline_mask)
    out["counterparty_concentration"] = _onesided((z_top1 + z_n) / 2, "high")

    z_m = _baseline_zscore(f["method_top1_share"], baseline_mask)
    out["method_concentration"] = _onesided((z_m + z_n) / 2, "high")

    out["burst_intensity"] = _onesided(
        _baseline_zscore(f["bursts_per_hour"], baseline_mask), "high"
    )

    out["drift_signal"] = _onesided(
        _baseline_zscore(f["new_counterparty_late_share"], baseline_mask), "high"
    )

    out["coordination"] = _onesided(
        _baseline_zscore(f["coordination_partner_count"], baseline_mask), "high"
    )

    return out


def _subscores(factors: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    """Roll the eight factor signals up into the six product-facing sub-scores."""
    sub = pd.DataFrame(index=factors.index)

    # Agent-likeness — machine-shaped behaviour: timing uniformity + gas
    # optimisation + repetitive method calls. This is descriptive, not
    # accusative — legitimate automation will score high here.
    sub["agent_likeness_score"] = (
        0.30 * factors["tod_uniformity_anomaly"]
        + 0.30 * factors["gas_tightness_anomaly"]
        + 0.20 * factors["method_concentration"]
        + 0.20 * factors["inter_arrival_anomaly"]
    )

    # Drift — late-window new counterparties + burstiness rising late.
    sub["drift_score"] = (
        0.65 * factors["drift_signal"]
        + 0.35 * factors["burst_intensity"]
    )

    # Coordination — neighbours within 60s, shared counterparties.
    sub["coordination_score"] = factors["coordination"]

    # Policy violation — wallet's payment behaviour exceeds what a delegated
    # agent baseline would do. We proxy this via:
    #   - large_value_share (top 5% of population values)
    #   - new_counterparty_late_share (paying a new vendor that wasn't
    #     pre-approved)
    # In a runtime product (memo 18), this becomes a hard rule check
    # against the agent's authorization_policy. Today it's a behavioural
    # proxy that fires on the same signals a policy engine would.
    large_share = features["large_value_share"].fillna(0.0).clip(0, 1)
    new_late_share = features["new_counterparty_late_share"].fillna(0.0).clip(0, 1)
    # 0 share -> 0 ; 0.10 share -> ~50 ; 0.30 share -> ~95.
    sub["policy_violation_score"] = (
        100.0 * (1 - np.exp(-large_share * 12))
        * 0.5
        + 100.0 * (1 - np.exp(-new_late_share * 12))
        * 0.5
    ).clip(0, 100)

    # Counterparty risk — top-1 share inflated by activity volume.
    sub["counterparty_risk_score"] = factors["counterparty_concentration"]

    # Prompt-injection — driven by a per-wallet tx-level flag set upstream
    # by the synthetic generator (the prompt_injected_invoice scenario) or
    # by a future product hook. Default 0 in real-data ingest paths.
    if "prompt_injection_share" in features.columns:
        share = features["prompt_injection_share"].fillna(0.0).clip(0, 1)
        sub["prompt_injection_score"] = (100.0 * (1 - np.exp(-share * 12))).clip(0, 100)
    else:
        sub["prompt_injection_score"] = 0.0

    return sub


def _explain(features: pd.Series, factors: pd.Series, sub: pd.Series, top_k: int = 3) -> tuple[list[dict], str]:
    """Return (top_factors_struct, one_sentence_explanation)."""
    top = sub.sort_values(ascending=False).head(top_k)
    top_factors: list[dict] = []
    fragments: list[str] = []
    for sub_name, sub_value in top.items():
        label = SUBSCORE_LABEL.get(sub_name, sub_name)
        top_factors.append({
            "name": sub_name,
            "label": label,
            "score": round(float(sub_value), 1),
        })
        if sub_value < 1.0:
            continue
        # Map sub-score back to its driving signal for the human-readable
        # fragment. Picks the most informative feature each time.
        if sub_name == "agent_likeness_score":
            fragments.append(
                f"{label} {sub_value:.0f}/100 "
                f"(KS {features['tod_uniformity_ks']:.2f}, "
                f"gas-to-basefee std {features['gas_to_basefee_std']:.3f})"
            )
        elif sub_name == "drift_score":
            fragments.append(
                f"{label} {sub_value:.0f}/100 "
                f"({features['new_counterparty_late_share']*100:.0f}% late-window new counterparties)"
            )
        elif sub_name == "coordination_score":
            fragments.append(
                f"{label} {sub_value:.0f}/100 "
                f"({int(features['coordination_partner_count'])} peers within 60s)"
            )
        elif sub_name == "policy_violation_score":
            fragments.append(
                f"{label} {sub_value:.0f}/100 "
                f"({features['large_value_share']*100:.0f}% > pop. p95)"
            )
        elif sub_name == "counterparty_risk_score":
            fragments.append(
                f"{label} {sub_value:.0f}/100 "
                f"({features['counterparty_top1_share']*100:.0f}% volume to top-1)"
            )
        elif sub_name == "prompt_injection_score":
            inj_share = features.get("prompt_injection_share", 0.0)
            fragments.append(
                f"{label} {sub_value:.0f}/100 "
                f"({inj_share*100:.0f}% of tx flagged as injected)"
            )
    sentence = "; ".join(fragments) if fragments else "No risk signal above threshold."
    return top_factors, sentence


def score_wallets(
    features: pd.DataFrame,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Return DataFrame with per-wallet six-vector + overall risk + tier + explanation.

    Output columns:
      overall_action_risk  -- composite (0-100)
      composite_score      -- alias for back-compat
      tier                 -- critical/high/medium/low
      <SUBSCORE_KEYS>      -- six sub-scores
      <FACTOR_KEYS>        -- legacy eight factor signals
      top_factors          -- list[dict] of top-3 sub-scores
      explanation          -- structured one-sentence string
    """
    weights = weights or SUBSCORE_WEIGHTS
    if len(features) == 0:
        return pd.DataFrame()

    factors = _factor_scores(features)
    subs = _subscores(factors, features)

    overall = np.zeros(len(features))
    for k, w in weights.items():
        overall = overall + subs[k].to_numpy() * w
    overall = pd.Series(np.clip(overall, 0, 100), index=features.index, name="overall_action_risk")

    tier = overall.apply(_suspicion_tier).rename("tier")

    top_factors_col: list[list[dict]] = []
    explanations: list[str] = []
    for addr in features.index:
        tf, sent = _explain(features.loc[addr], factors.loc[addr], subs.loc[addr])
        top_factors_col.append(tf)
        explanations.append(sent)

    out = pd.concat([overall, tier, subs, factors], axis=1)
    out["composite_score"] = overall  # back-compat alias
    out["top_factors"] = top_factors_col
    out["explanation"] = explanations
    out = out.sort_values("overall_action_risk", ascending=False)
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
        print(f"  {addr[:10]} | overall {row['overall_action_risk']:5.1f} | {row['tier']:8} | {row['explanation']}")


if __name__ == "__main__":
    main()
