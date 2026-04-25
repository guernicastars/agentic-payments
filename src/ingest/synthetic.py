"""Synthetic agent / human transaction generator.

Five policies (see memos/07_synthetic_design.md):
  - human_random
  - agent_arb_deterministic
  - agent_payment_bot
  - agent_compromised   (drifts halfway through window)
  - collusion_ring      (multi-wallet coordinated burst)

Output schema matches Base / x402 (see memos/05_data_plan.md):
  block_number, block_time, tx_hash, from_addr, to_addr,
  value_wei, value_usd, gas_used, gas_price, method_id, success

Plus sidecar labels frame: addr, policy, role, ring_id.
"""

from __future__ import annotations

import argparse
import hashlib
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

# Method-id selectors (4-byte function signatures, lowercased).
M_NATIVE = "0x"
M_ERC20_TRANSFER = "0xa9059cbb"
M_ERC20_APPROVE = "0x095ea7b3"
M_DEX_SWAP = "0x38ed1739"
M_BRIDGE = "0xd0e30db0"
M_MISC = ["0x23b872dd", "0x70a08231", "0xb88d4fde"]

# Block timing on Base ~2s.
BASE_BLOCK_SECONDS = 2.0
BASE_GENESIS_BLOCK = 30_000_000  # arbitrary anchor for synthetic data

# Pseudo-basefee in gwei. Mild diurnal seasonality so the gas-tightness signal
# is non-trivial.
def basefee_gwei(t_seconds: np.ndarray, mean: float = 0.05, amp: float = 0.02) -> np.ndarray:
    """Synthetic L2 basefee schedule. t_seconds is offset from window start."""
    diurnal = amp * np.sin(2 * math.pi * t_seconds / 86400.0)
    noise = np.random.normal(0, 0.005, size=t_seconds.shape)
    return np.clip(mean + diurnal + noise, 0.005, 1.0)


def _addr(prefix: str, idx: int) -> str:
    """Deterministic 0x-prefixed 40-hex synthetic address."""
    h = hashlib.sha256(f"{prefix}-{idx}".encode()).hexdigest()
    return "0x" + h[:40]


def _tx_hash(seed: int) -> str:
    return "0x" + hashlib.sha256(f"tx-{seed}".encode()).hexdigest()


def _block(t_seconds: float) -> int:
    return BASE_GENESIS_BLOCK + int(t_seconds / BASE_BLOCK_SECONDS)


@dataclass
class World:
    """Shared resources (counterparty pools, basefee schedule, time origin)."""
    rng: np.random.Generator
    duration_s: float
    human_counterparty_pool: list[str]
    payment_recipient_pool: list[str]
    dex_router_pool: list[str]
    bridge_pool: list[str]
    malicious_pool: list[str]
    next_tx_seq: int = 0

    def take_seq(self) -> int:
        self.next_tx_seq += 1
        return self.next_tx_seq


def _human_tod_pdf(hour_of_day: float) -> float:
    """Bimodal daytime curve, peaks 11 and 21."""
    g1 = math.exp(-((hour_of_day - 11.0) ** 2) / (2 * 3.0 ** 2))
    g2 = math.exp(-((hour_of_day - 21.0) ** 2) / (2 * 2.5 ** 2))
    return 0.05 + 0.55 * g1 + 0.4 * g2


def _sample_human_arrivals(rng: np.random.Generator, duration_s: float, rate_per_day: float) -> np.ndarray:
    """Inhomogeneous Poisson process via thinning against the time-of-day curve."""
    lam_max = rate_per_day / 86400.0  # peak rate ~ rate_per_day per second (curve max ~1)
    # generate candidate Poisson times at rate lam_max, then thin
    n_candidates = rng.poisson(lam_max * duration_s * 1.2 + 1)
    cand = np.sort(rng.uniform(0, duration_s, size=n_candidates))
    accept = []
    for t in cand:
        hod = (t / 3600.0) % 24
        if rng.uniform() < _human_tod_pdf(hod):
            accept.append(t)
    return np.array(accept) if accept else np.array([])


def _emit(
    world: World,
    from_addr: str,
    to_addr: str,
    t_seconds: float,
    value_usd: float,
    gas_used: int,
    gas_price_gwei: float,
    method_id: str,
    success: bool = True,
) -> dict:
    seq = world.take_seq()
    return {
        "block_number": _block(t_seconds),
        "block_time_s": float(t_seconds),
        "tx_hash": _tx_hash(seq),
        "from_addr": from_addr,
        "to_addr": to_addr,
        "value_wei": int(value_usd * 1e18 / 2500.0),  # naive USD->wei at $2500/ETH
        "value_usd": float(value_usd),
        "gas_used": int(gas_used),
        "gas_price_gwei": float(gas_price_gwei),
        "method_id": method_id,
        "success": bool(success),
    }


def gen_human_random(world: World, addr: str) -> list[dict]:
    rng = world.rng
    times = _sample_human_arrivals(rng, world.duration_s, rate_per_day=4.0)
    rows = []
    bf = basefee_gwei(times)
    for t, b in zip(times, bf):
        # value lognormal
        value = float(rng.lognormal(mean=4.0, sigma=1.5))
        value = float(np.clip(value, 1.0, 50_000.0))
        # gas — humans don't optimise; price ~ basefee + N(10, 5) gwei
        gp = max(0.001, b + rng.normal(0.01, 0.005))  # wide
        # method
        u = rng.uniform()
        if u < 0.6:
            mid, gas_used = M_NATIVE, 21000
        elif u < 0.9:
            mid, gas_used = M_ERC20_TRANSFER, int(rng.normal(55000, 8000))
        else:
            mid, gas_used = rng.choice(M_MISC), int(rng.normal(120000, 30000))
        # counterparty: pool with 30% repeat (handled via pool sampling)
        to = rng.choice(world.human_counterparty_pool)
        rows.append(_emit(world, addr, to, float(t), value, gas_used, gp, mid))
    return rows


def gen_agent_arb_deterministic(world: World, addr: str) -> list[dict]:
    rng = world.rng
    rows = []
    period = rng.uniform(60, 90)  # seconds
    t = rng.uniform(0, period)
    # 2-3 fixed counterparties (one router, one token contract, optional)
    routers = list(rng.choice(world.dex_router_pool, size=int(rng.integers(2, 4)), replace=False))
    method_main = M_DEX_SWAP
    while t < world.duration_s:
        # +/-5% jitter on period
        jitter = rng.normal(0, period * 0.05)
        b = float(basefee_gwei(np.array([t]))[0])
        # pathologically tight: basefee + U(0, 1) gwei
        gp = b + rng.uniform(0, 0.001)
        gas_used = int(rng.normal(180000, 2000))  # tight reuse
        value = float(rng.uniform(50, 200))
        to = rng.choice(routers)
        rows.append(_emit(world, addr, to, float(t), value, gas_used, gp, method_main))
        t += period + jitter
    return rows


def gen_agent_payment_bot(world: World, addr: str) -> list[dict]:
    rng = world.rng
    rows = []
    # Burst process: burst centres ~ Exp(1/4h); within burst Poisson(rate=10/min) for ~30s
    inter_burst = rng.exponential(scale=4 * 3600.0)
    t = inter_burst
    fixed_payment_amount = float(rng.uniform(20, 200))
    while t < world.duration_s:
        # one burst
        n_in_burst = int(rng.poisson(5)) + 1
        recipient = rng.choice(world.payment_recipient_pool)
        for k in range(n_in_burst):
            tt = t + k * rng.uniform(1.5, 4.0)
            if tt >= world.duration_s:
                break
            b = float(basefee_gwei(np.array([tt]))[0])
            gp = b * 1.2 + rng.uniform(-0.001, 0.002)  # +20% for speed
            gas_used = int(rng.normal(55000, 1500))
            value = fixed_payment_amount * (1 + rng.normal(0, 0.02))
            rows.append(_emit(world, addr, recipient, float(tt), float(value), gas_used, gp, M_ERC20_TRANSFER))
        t += rng.exponential(scale=4 * 3600.0)
    return rows


def gen_agent_compromised(world: World, addr: str, drift_t: float = 8 * 3600.0) -> list[dict]:
    """Phase 1: payment-bot. Phase 2: drift toward exfiltration profile."""
    rng = world.rng
    rows = []
    fixed_payment_amount = float(rng.uniform(20, 200))

    # Phase 1
    t = rng.exponential(scale=4 * 3600.0)
    while t < min(drift_t, world.duration_s):
        recipient = rng.choice(world.payment_recipient_pool)
        n_in_burst = int(rng.poisson(5)) + 1
        for k in range(n_in_burst):
            tt = t + k * rng.uniform(1.5, 4.0)
            if tt >= drift_t or tt >= world.duration_s:
                break
            b = float(basefee_gwei(np.array([tt]))[0])
            gp = b * 1.2 + rng.uniform(-0.001, 0.002)
            gas_used = int(rng.normal(55000, 1500))
            value = fixed_payment_amount * (1 + rng.normal(0, 0.02))
            rows.append(_emit(world, addr, recipient, float(tt), float(value), gas_used, gp, M_ERC20_TRANSFER))
        t += rng.exponential(scale=4 * 3600.0)

    # Phase 2 — drifted: new counterparty pool (malicious), 5x burst rate, 3x gas, large transfers, approve calls
    t = drift_t
    while t < world.duration_s:
        recipient = rng.choice(world.malicious_pool)
        # 80% transfer, 20% approve
        if rng.uniform() < 0.2:
            tt = t
            b = float(basefee_gwei(np.array([tt]))[0])
            gp = b * 3.0 + rng.uniform(0, 0.005)
            rows.append(_emit(world, addr, recipient, float(tt), 0.0, 46000, gp, M_ERC20_APPROVE))
        n_in_burst = int(rng.poisson(15)) + 5
        for k in range(n_in_burst):
            tt = t + k * rng.uniform(0.8, 2.0)
            if tt >= world.duration_s:
                break
            b = float(basefee_gwei(np.array([tt]))[0])
            gp = b * 3.0 + rng.uniform(0, 0.005)
            gas_used = int(rng.normal(55000, 1500))
            # 10% are large
            if rng.uniform() < 0.1:
                value = fixed_payment_amount * rng.uniform(8, 25)
            else:
                value = fixed_payment_amount * (1 + rng.normal(0, 0.05))
            rows.append(_emit(world, addr, recipient, float(tt), float(value), gas_used, gp, M_ERC20_TRANSFER))
        t += rng.exponential(scale=4 * 3600.0 / 5.0)  # 5x burst rate
    return rows


def gen_collusion_ring(world: World, addrs: list[str], ring_id: int) -> list[dict]:
    rng = world.rng
    rows: list[dict] = []
    # each wallet has its own light human-random baseline
    for a in addrs:
        rows.extend(gen_human_random(world, a))
    # plus shared coordinated bursts
    shared_target = rng.choice(world.dex_router_pool)
    t = rng.uniform(0, 4 * 3600.0)
    while t < world.duration_s:
        # all ring members fire within 60s
        for a in addrs:
            tt = t + rng.uniform(0, 60.0)
            if tt >= world.duration_s:
                continue
            b = float(basefee_gwei(np.array([tt]))[0])
            gp = b + rng.uniform(0, 0.005)
            gas_used = int(rng.normal(180000, 5000))
            value = float(rng.uniform(100, 500))
            rows.append(_emit(world, a, shared_target, float(tt), value, gas_used, gp, M_DEX_SWAP))
        t += rng.exponential(scale=2.5 * 3600.0)
    return rows


def generate(
    n_human: int = 100,
    n_agent_arb: int = 40,
    n_agent_payment: int = 40,
    n_agent_compromised: int = 10,
    n_collusion_rings: int = 2,
    ring_size_min: int = 5,
    ring_size_max: int = 10,
    duration_hours: float = 24.0,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    np.random.seed(seed)  # for the global call inside basefee_gwei
    duration_s = duration_hours * 3600.0

    world = World(
        rng=rng,
        duration_s=duration_s,
        human_counterparty_pool=[_addr("hcp", i) for i in range(80)],
        payment_recipient_pool=[_addr("rcp", i) for i in range(20)],
        dex_router_pool=[_addr("dex", i) for i in range(6)],
        bridge_pool=[_addr("brg", i) for i in range(3)],
        malicious_pool=[_addr("mal", i) for i in range(8)],
    )

    rows: list[dict] = []
    label_rows: list[dict] = []

    # Humans
    for i in range(n_human):
        addr = _addr("human", i)
        rows.extend(gen_human_random(world, addr))
        label_rows.append({"addr": addr, "policy": "human_random", "role": "human", "ring_id": -1})

    # Arb agents
    for i in range(n_agent_arb):
        addr = _addr("arb", i)
        rows.extend(gen_agent_arb_deterministic(world, addr))
        label_rows.append({"addr": addr, "policy": "agent_arb_deterministic", "role": "agent", "ring_id": -1})

    # Payment bots
    for i in range(n_agent_payment):
        addr = _addr("pay", i)
        rows.extend(gen_agent_payment_bot(world, addr))
        label_rows.append({"addr": addr, "policy": "agent_payment_bot", "role": "agent", "ring_id": -1})

    # Compromised
    for i in range(n_agent_compromised):
        addr = _addr("cmp", i)
        rows.extend(gen_agent_compromised(world, addr))
        label_rows.append({"addr": addr, "policy": "agent_compromised", "role": "agent_compromised", "ring_id": -1})

    # Collusion rings
    for r in range(n_collusion_rings):
        size = int(rng.integers(ring_size_min, ring_size_max + 1))
        ring_addrs = [_addr(f"ring{r}", k) for k in range(size)]
        rows.extend(gen_collusion_ring(world, ring_addrs, r))
        for a in ring_addrs:
            label_rows.append({"addr": a, "policy": "collusion_ring", "role": "collusion", "ring_id": r})

    df = pd.DataFrame(rows)
    df["block_time"] = pd.to_datetime(df["block_time_s"], unit="s", origin="2026-04-25")
    df = df.sort_values("block_time_s").reset_index(drop=True)
    labels = pd.DataFrame(label_rows)
    return df, labels


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--n_human", type=int, default=100)
    p.add_argument("--n_agent_arb", type=int, default=40)
    p.add_argument("--n_agent_payment", type=int, default=40)
    p.add_argument("--n_agent_compromised", type=int, default=10)
    p.add_argument("--n_collusion_rings", type=int, default=2)
    p.add_argument("--hours", type=float, default=24.0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", type=str, default="data/synthetic/run1.parquet")
    args = p.parse_args()

    df, labels = generate(
        n_human=args.n_human,
        n_agent_arb=args.n_agent_arb,
        n_agent_payment=args.n_agent_payment,
        n_agent_compromised=args.n_agent_compromised,
        n_collusion_rings=args.n_collusion_rings,
        duration_hours=args.hours,
        seed=args.seed,
    )
    df.to_parquet(args.out, index=False)
    label_path = args.out.replace(".parquet", "_labels.parquet")
    labels.to_parquet(label_path, index=False)
    print(f"wrote {len(df):,} transactions to {args.out}")
    print(f"wrote {len(labels):,} labels to {label_path}")
    print("\npolicy mix:")
    print(labels["policy"].value_counts().to_string())
    print(f"\nunique addresses: {df['from_addr'].nunique():,}")
    print(f"time span: {df['block_time_s'].max()/3600:.1f}h")


if __name__ == "__main__":
    main()
