"""Wallet clustering for coordinated agent detection.

Adapted from polymarket/pipeline/jobs/wallet_analyzer.py. Same composite
similarity = 0.3·counterparty_overlap + 0.4·method_agreement + 0.3·timing_correlation,
greedy edge construction with min thresholds, then connected-component grouping.

Replaces ClickHouse reads with DataFrame inputs. Replaces market/side semantics
with counterparty/method semantics — agents share counterparty contracts and
4-byte method selectors the way prediction-market wallets share condition_ids
and trade sides.
"""

from __future__ import annotations

import argparse
import uuid
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd
import networkx as nx


CLUSTER_MIN_OVERLAP = 0.10
CLUSTER_MIN_SIMILARITY = 0.40
CLUSTER_TIME_WINDOW_S = 60.0
MAX_WALLETS_FOR_PAIRWISE = 500  # cap to keep O(n^2) tractable


@dataclass
class ClusterResult:
    cluster_id: str
    wallets: list[str]
    size: int
    similarity_score: float
    timing_corr: float
    counterparty_overlap: float
    method_agreement: float
    common_counterparties: list[str]


def _wallet_profiles(txs: pd.DataFrame, min_tx: int = 3) -> dict[str, dict]:
    """Per-wallet bag of (counterparty, method, timestamp) tuples and counterparty sets."""
    profiles: dict[str, dict] = {}
    for addr, g in txs.groupby("from_addr"):
        if len(g) < min_tx:
            continue
        profiles[addr] = {
            "events": list(zip(g["to_addr"], g["method_id"], g["block_time_s"].astype(float))),
            "counterparties": set(g["to_addr"].unique()),
            "tx_count": len(g),
        }
    return profiles


def _pair_similarity(p1: dict, p2: dict, time_window: float) -> dict:
    cps_1 = p1["counterparties"]
    cps_2 = p2["counterparties"]
    shared = cps_1 & cps_2
    all_cps = cps_1 | cps_2
    overlap = len(shared) / len(all_cps) if all_cps else 0.0
    if len(shared) < 2:
        return {"similarity": 0.0, "overlap": overlap, "method_agree": 0.0,
                "timing_corr": 0.0, "shared_count": len(shared), "shared": list(shared)}

    # Method agreement: per shared counterparty, what fraction of method-id usages match
    p1_methods = defaultdict(set)
    p2_methods = defaultdict(set)
    for cp, m, _ in p1["events"]:
        if cp in shared:
            p1_methods[cp].add(m)
    for cp, m, _ in p2["events"]:
        if cp in shared:
            p2_methods[cp].add(m)
    agree = 0
    for cp in shared:
        if p1_methods[cp] & p2_methods[cp]:
            agree += 1
    method_agree = agree / len(shared) if shared else 0.0

    # Timing correlation: per shared counterparty, fraction of (t1, t2) pairs within window
    timing_matches = 0
    timing_total = 0
    p1_times = defaultdict(list)
    p2_times = defaultdict(list)
    for cp, _, t in p1["events"]:
        if cp in shared:
            p1_times[cp].append(t)
    for cp, _, t in p2["events"]:
        if cp in shared:
            p2_times[cp].append(t)
    for cp in shared:
        t1s = sorted(p1_times[cp])
        t2s = sorted(p2_times[cp])
        # capped pairwise to avoid O(N^2) on heavy wallets
        max_per = 50
        for t1 in t1s[:max_per]:
            for t2 in t2s[:max_per]:
                timing_total += 1
                if abs(t1 - t2) <= time_window:
                    timing_matches += 1
    timing_corr = timing_matches / timing_total if timing_total > 0 else 0.0

    similarity = 0.3 * overlap + 0.4 * method_agree + 0.3 * timing_corr
    return {
        "similarity": similarity,
        "overlap": overlap,
        "method_agree": method_agree,
        "timing_corr": timing_corr,
        "shared_count": len(shared),
        "shared": list(shared)[:20],
    }


def cluster_wallets(
    txs: pd.DataFrame,
    min_overlap: float = CLUSTER_MIN_OVERLAP,
    min_similarity: float = CLUSTER_MIN_SIMILARITY,
    time_window_s: float = CLUSTER_TIME_WINDOW_S,
    max_wallets: int = MAX_WALLETS_FOR_PAIRWISE,
) -> tuple[list[ClusterResult], pd.DataFrame]:
    """Greedy pairwise clustering.

    Returns:
      clusters: connected components above threshold (size ≥ 2)
      edge_df: every pair above (overlap, similarity) thresholds — useful for viz
    """
    profiles = _wallet_profiles(txs)
    wallets = sorted(profiles, key=lambda w: -profiles[w]["tx_count"])[:max_wallets]

    G = nx.Graph()
    G.add_nodes_from(wallets)
    edge_rows = []

    for i in range(len(wallets)):
        for j in range(i + 1, len(wallets)):
            w1, w2 = wallets[i], wallets[j]
            sim = _pair_similarity(profiles[w1], profiles[w2], time_window_s)
            if sim["overlap"] < min_overlap:
                continue
            if sim["similarity"] < min_similarity:
                continue
            G.add_edge(w1, w2, **sim)
            edge_rows.append({
                "w1": w1, "w2": w2,
                "similarity": sim["similarity"],
                "overlap": sim["overlap"],
                "method_agree": sim["method_agree"],
                "timing_corr": sim["timing_corr"],
                "shared_count": sim["shared_count"],
            })

    edge_df = pd.DataFrame(edge_rows)
    clusters: list[ClusterResult] = []
    for component in nx.connected_components(G):
        members = [w for w in component if G.degree(w) > 0]
        if len(members) < 2:
            continue
        # average pairwise stats across edges in component
        sub = G.subgraph(members)
        sims = [d["similarity"] for _, _, d in sub.edges(data=True)]
        ov = [d["overlap"] for _, _, d in sub.edges(data=True)]
        ma = [d["method_agree"] for _, _, d in sub.edges(data=True)]
        tc = [d["timing_corr"] for _, _, d in sub.edges(data=True)]
        common: set[str] = set()
        for _, _, d in sub.edges(data=True):
            common.update(d["shared"])
        clusters.append(ClusterResult(
            cluster_id=str(uuid.uuid4()),
            wallets=sorted(members),
            size=len(members),
            similarity_score=float(np.mean(sims)),
            timing_corr=float(np.mean(tc)),
            counterparty_overlap=float(np.mean(ov)),
            method_agreement=float(np.mean(ma)),
            common_counterparties=sorted(common)[:20],
        ))
    clusters.sort(key=lambda c: -c.similarity_score)
    return clusters, edge_df


def clusters_to_df(clusters: list[ClusterResult]) -> pd.DataFrame:
    rows = []
    for c in clusters:
        for w in c.wallets:
            rows.append({
                "cluster_id": c.cluster_id,
                "from_addr": w,
                "size": c.size,
                "similarity_score": c.similarity_score,
                "timing_corr": c.timing_corr,
                "counterparty_overlap": c.counterparty_overlap,
                "method_agreement": c.method_agreement,
            })
    return pd.DataFrame(rows)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=str, help="path to txs parquet")
    p.add_argument("-o", "--out", type=str, default="data/processed/clusters.parquet")
    p.add_argument("--edges_out", type=str, default="data/processed/cluster_edges.parquet")
    p.add_argument("--min_similarity", type=float, default=CLUSTER_MIN_SIMILARITY)
    p.add_argument("--min_overlap", type=float, default=CLUSTER_MIN_OVERLAP)
    args = p.parse_args()

    txs = pd.read_parquet(args.input)
    clusters, edges = cluster_wallets(txs, min_overlap=args.min_overlap, min_similarity=args.min_similarity)
    df = clusters_to_df(clusters)
    df.to_parquet(args.out)
    if len(edges) > 0:
        edges.to_parquet(args.edges_out)
    print(f"found {len(clusters)} clusters covering {len(df)} wallets")
    if clusters:
        print("\ntop clusters:")
        for c in clusters[:5]:
            print(f"  {c.cluster_id[:8]} | size={c.size} sim={c.similarity_score:.3f} timing={c.timing_corr:.3f} overlap={c.counterparty_overlap:.3f}")


if __name__ == "__main__":
    main()
