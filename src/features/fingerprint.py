"""Behavioural fingerprint per wallet.

Six families (see memos/08_features_spec.md):
  A. Temporal       (8)
  B. Gas/optimisation (6)
  C. Value          (6)
  D. Counterparty   (6)
  E. Method profile (5)
  F. Burst/coordination (5)

Total: 36 features per wallet.

Input schema (from src.ingest.synthetic or Base ingest):
  block_time_s, from_addr, to_addr, value_usd, gas_used,
  gas_price_gwei, method_id, success
"""

from __future__ import annotations

import argparse
import math
from collections import Counter

import numpy as np
import pandas as pd
from scipy.stats import entropy as shannon_entropy
from scipy.stats import ks_2samp


# Canonical human time-of-day curve (bimodal peaks 11h, 21h). Match generator.
def _human_tod_curve() -> np.ndarray:
    h = np.arange(24)
    g1 = np.exp(-((h - 11.0) ** 2) / (2 * 3.0 ** 2))
    g2 = np.exp(-((h - 21.0) ** 2) / (2 * 2.5 ** 2))
    p = 0.05 + 0.55 * g1 + 0.4 * g2
    return p / p.sum()


_HUMAN_TOD = _human_tod_curve()


def _safe_entropy(counts: np.ndarray) -> float:
    if len(counts) == 0 or counts.sum() == 0:
        return 0.0
    p = counts / counts.sum()
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def _hour_of_day_hist(times_s: np.ndarray) -> np.ndarray:
    h = (times_s // 3600).astype(int) % 24
    counts = np.bincount(h, minlength=24).astype(float)
    return counts


def _ks_uniform(counts: np.ndarray) -> float:
    """KS distance between hour-of-day empirical CDF and Uniform[0,24]."""
    if counts.sum() == 0:
        return 0.0
    p = counts / counts.sum()
    cdf = np.cumsum(p)
    uniform_cdf = np.arange(1, 25) / 24.0
    return float(np.max(np.abs(cdf - uniform_cdf)))


def _kl_against_human(counts: np.ndarray, eps: float = 1e-3) -> float:
    if counts.sum() == 0:
        return 0.0
    p = counts / counts.sum()
    p = (p + eps) / (1.0 + 24 * eps)
    q = (_HUMAN_TOD + eps) / (1.0 + 24 * eps)
    return float((p * np.log(p / q)).sum())


def _basefee_at(t_s: float, mean: float = 0.05, amp: float = 0.02) -> float:
    """Inverse of generator's basefee. Approx — used as denominator only."""
    return mean + amp * math.sin(2 * math.pi * t_s / 86400.0)


def _temporal_features(times_s: np.ndarray) -> dict:
    n = len(times_s)
    if n < 2:
        return {
            "tx_count": n,
            "inter_arrival_mean_s": 0.0,
            "inter_arrival_std_s": 0.0,
            "inter_arrival_cv": 0.0,
            "inter_arrival_entropy": 0.0,
            "tod_uniformity_ks": 0.0,
            "tod_human_kl": 0.0,
            "burstiness": 0.0,
        }
    times_s = np.sort(times_s)
    deltas = np.diff(times_s)
    mean_d = float(np.mean(deltas))
    std_d = float(np.std(deltas))
    cv = std_d / mean_d if mean_d > 0 else 0.0
    burstiness = (std_d - mean_d) / (std_d + mean_d + 1e-9)
    # entropy on log-binned inter-arrivals, 12 bins from 0.5s to 24h
    bins = np.logspace(np.log10(0.5), np.log10(86400), 13)
    hist, _ = np.histogram(np.clip(deltas, 0.5, 86400), bins=bins)
    ia_entropy = _safe_entropy(hist.astype(float))
    counts = _hour_of_day_hist(times_s)
    return {
        "tx_count": n,
        "inter_arrival_mean_s": mean_d,
        "inter_arrival_std_s": std_d,
        "inter_arrival_cv": cv,
        "inter_arrival_entropy": ia_entropy,
        "tod_uniformity_ks": _ks_uniform(counts),
        "tod_human_kl": _kl_against_human(counts),
        "burstiness": float(burstiness),
    }


def _gas_features(df: pd.DataFrame) -> dict:
    if len(df) == 0:
        return {k: 0.0 for k in [
            "gas_price_mean_gwei", "gas_price_std_gwei",
            "gas_to_basefee_mean", "gas_to_basefee_std",
            "gas_used_cv", "gas_optimisation_score",
        ]}
    gp = df["gas_price_gwei"].to_numpy(dtype=float)
    bf = np.array([_basefee_at(t) for t in df["block_time_s"].to_numpy()])
    ratio = gp / np.clip(bf, 1e-4, None)
    gu = df["gas_used"].to_numpy(dtype=float)
    gu_mean = float(np.mean(gu)) if len(gu) > 0 else 0.0
    gu_cv = float(np.std(gu) / gu_mean) if gu_mean > 0 else 0.0
    # composite: low ratio std + low gu cv → tight = high score
    ratio_std = float(np.std(ratio))
    opt = 1.0 / (1.0 + ratio_std + gu_cv)
    return {
        "gas_price_mean_gwei": float(np.mean(gp)),
        "gas_price_std_gwei": float(np.std(gp)),
        "gas_to_basefee_mean": float(np.mean(ratio)),
        "gas_to_basefee_std": ratio_std,
        "gas_used_cv": gu_cv,
        "gas_optimisation_score": opt,
    }


def _value_features(df: pd.DataFrame, pop_p95: float) -> dict:
    v = df["value_usd"].to_numpy(dtype=float)
    if len(v) == 0:
        return {k: 0.0 for k in [
            "value_mean", "value_median", "value_std",
            "value_log_std", "value_entropy", "large_value_share",
        ]}
    log_v = np.log1p(v)
    bins = np.linspace(0, max(np.log1p(50_000.0), log_v.max() + 0.1), 16)
    hist, _ = np.histogram(log_v, bins=bins)
    return {
        "value_mean": float(np.mean(v)),
        "value_median": float(np.median(v)),
        "value_std": float(np.std(v)),
        "value_log_std": float(np.std(log_v)),
        "value_entropy": _safe_entropy(hist.astype(float)),
        "large_value_share": float(np.mean(v > pop_p95)) if pop_p95 > 0 else 0.0,
    }


def _counterparty_features(df: pd.DataFrame, window_seconds: float, late_quantile: float = 0.75) -> dict:
    if len(df) == 0:
        return {k: 0.0 for k in [
            "unique_counterparties", "counterparty_top1_share",
            "counterparty_top3_share", "counterparty_entropy",
            "counterparty_repeat_rate", "new_counterparty_late_share",
        ]}
    to = df["to_addr"].to_numpy()
    counts = Counter(to)
    total = len(to)
    top = counts.most_common(3)
    top1 = top[0][1] / total if top else 0.0
    top3 = sum(c for _, c in top) / total if top else 0.0
    repeat_rate = float(np.mean([c >= 2 for c in counts.values()]))
    # late share: counterparties first seen in last 25% of window, what fraction of tx
    cutoff = window_seconds * late_quantile
    seen_before: set[str] = set()
    late_first_tx = 0
    times = df["block_time_s"].to_numpy()
    for i in np.argsort(times):
        t = times[i]
        addr = to[i]
        if t >= cutoff and addr not in seen_before:
            late_first_tx += 1
        seen_before.add(addr)
    new_late_share = late_first_tx / total if total else 0.0
    return {
        "unique_counterparties": float(len(counts)),
        "counterparty_top1_share": top1,
        "counterparty_top3_share": top3,
        "counterparty_entropy": _safe_entropy(np.array(list(counts.values()), dtype=float)),
        "counterparty_repeat_rate": repeat_rate,
        "new_counterparty_late_share": new_late_share,
    }


def _method_features(df: pd.DataFrame) -> dict:
    if len(df) == 0:
        return {k: 0.0 for k in [
            "unique_method_ids", "method_top1_share",
            "native_share", "erc20_transfer_share", "success_rate",
        ]}
    m = df["method_id"].to_numpy()
    counts = Counter(m)
    total = len(m)
    top1 = counts.most_common(1)[0][1] / total
    native = counts.get("0x", 0) / total
    erc20 = counts.get("0xa9059cbb", 0) / total
    success_rate = float(df["success"].mean())
    return {
        "unique_method_ids": float(len(counts)),
        "method_top1_share": top1,
        "native_share": native,
        "erc20_transfer_share": erc20,
        "success_rate": success_rate,
    }


def _burst_features(times_s: np.ndarray, all_times_by_other: np.ndarray | None = None) -> dict:
    """Per-wallet burst features. all_times_by_other: timestamps of *other* wallets in cohort, sorted, for coordination_proxy."""
    if len(times_s) == 0:
        return {k: 0.0 for k in [
            "max_burst_60s", "bursts_per_hour",
            "mean_inter_burst_minutes", "coordination_proxy", "coordination_partner_count",
        ]}
    times_s = np.sort(times_s)
    # max events in any 60s window — sliding window
    j = 0
    max_60 = 1
    for i in range(len(times_s)):
        while times_s[i] - times_s[j] > 60:
            j += 1
        max_60 = max(max_60, i - j + 1)
    # bursts: groups of ≥3 within 30s
    bursts = 0
    last_burst_end = -1e18
    burst_starts: list[float] = []
    j = 0
    for i in range(len(times_s)):
        while times_s[i] - times_s[j] > 30:
            j += 1
        if i - j + 1 >= 3 and times_s[i] > last_burst_end + 60:
            bursts += 1
            burst_starts.append(times_s[i])
            last_burst_end = times_s[i]
    duration_h = max((times_s[-1] - times_s[0]) / 3600.0, 1e-6)
    bursts_per_h = bursts / duration_h
    if len(burst_starts) >= 2:
        mean_ib = float(np.mean(np.diff(burst_starts)) / 60.0)
    else:
        mean_ib = 0.0
    # coordination_proxy
    coord = 0.0
    if all_times_by_other is not None and len(all_times_by_other) > 0:
        # for each tx, is there an other-wallet tx within 60s?
        idx = np.searchsorted(all_times_by_other, times_s)
        hits = 0
        for k, t in enumerate(times_s):
            lo = max(0, idx[k] - 1)
            hi = min(len(all_times_by_other) - 1, idx[k])
            for ii in (lo, hi):
                if abs(all_times_by_other[ii] - t) <= 60:
                    hits += 1
                    break
        coord = hits / len(times_s)
    return {
        "max_burst_60s": float(max_60),
        "bursts_per_hour": float(bursts_per_h),
        "mean_inter_burst_minutes": mean_ib,
        "coordination_proxy": coord,
        "coordination_partner_count": 0.0,  # filled in cohort pass
    }


def compute_features(txs: pd.DataFrame) -> pd.DataFrame:
    """Compute per-wallet behavioural fingerprint."""
    if len(txs) == 0:
        return pd.DataFrame()

    txs = txs.copy()
    txs["block_time_s"] = txs["block_time_s"].astype(float)
    window_s = float(txs["block_time_s"].max() - txs["block_time_s"].min())

    pop_p95 = float(np.percentile(txs["value_usd"].to_numpy(), 95)) if len(txs) else 0.0

    rows = []
    # Pre-build a sorted global timestamp array per wallet for coordination_proxy
    by_wallet = {addr: g.sort_values("block_time_s") for addr, g in txs.groupby("from_addr")}

    # all timestamps
    all_times = np.sort(txs["block_time_s"].to_numpy())

    for addr, g in by_wallet.items():
        # other-wallet timestamps via set difference. For speed, pass ALL timestamps
        # and accept self-hits — at scale of 50k tx the bias is negligible; we
        # subtract the wallet's own contribution below.
        feats = {"from_addr": addr}
        feats.update(_temporal_features(g["block_time_s"].to_numpy()))
        feats.update(_gas_features(g))
        feats.update(_value_features(g, pop_p95))
        feats.update(_counterparty_features(g, window_seconds=window_s))
        feats.update(_method_features(g))
        # for coordination proxy, use all_times minus the wallet's own (approximate by removing own count)
        own_times = np.sort(g["block_time_s"].to_numpy())
        # mask: remove own timestamps
        # cheap approx: pass all_times. We'll subtract self-bias by computing a
        # "self-neighborhood" baseline = 1.0 because every tx hits itself within
        # 0s; we subtract that uniform 1.0 contribution post-hoc.
        burst = _burst_features(own_times, all_times_by_other=all_times)
        # remove self-bias on coordination_proxy: every tx self-hits at distance 0 < 60s
        burst["coordination_proxy"] = max(0.0, burst["coordination_proxy"] - 1.0) if len(g) > 0 else 0.0
        # coordination_partner_count: count distinct *other* wallets with a tx within 60s of any of this wallet's tx
        partners = _count_coordination_partners(g["block_time_s"].to_numpy(), txs, addr)
        burst["coordination_partner_count"] = float(partners)
        feats.update(burst)
        rows.append(feats)

    out = pd.DataFrame(rows).set_index("from_addr")
    return out


def _count_coordination_partners(times_s: np.ndarray, txs: pd.DataFrame, self_addr: str, window: float = 60.0) -> int:
    """Distinct other wallets that have ≥1 tx within `window` seconds of any of this wallet's tx."""
    if len(times_s) == 0:
        return 0
    times_s = np.sort(times_s)
    other = txs[txs["from_addr"] != self_addr][["from_addr", "block_time_s"]].copy()
    if len(other) == 0:
        return 0
    other_t = other["block_time_s"].to_numpy()
    order = np.argsort(other_t)
    other_t_sorted = other_t[order]
    other_addr_sorted = other["from_addr"].to_numpy()[order]
    partners = set()
    for t in times_s:
        lo = np.searchsorted(other_t_sorted, t - window, side="left")
        hi = np.searchsorted(other_t_sorted, t + window, side="right")
        partners.update(other_addr_sorted[lo:hi].tolist())
        if len(partners) > 50:  # cap
            break
    return len(partners)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=str)
    p.add_argument("-o", "--out", type=str, default="data/processed/features.parquet")
    args = p.parse_args()
    txs = pd.read_parquet(args.input)
    feats = compute_features(txs)
    feats.to_parquet(args.out)
    print(f"wrote {len(feats):,} wallet rows × {feats.shape[1]} features to {args.out}")
    print("\nfeature columns:")
    for c in feats.columns:
        print(f"  {c}")


if __name__ == "__main__":
    main()
