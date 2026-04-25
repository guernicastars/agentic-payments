# 07 — Synthetic agent traffic generator design

**Date:** 2026-04-25

## Why synthetic-first

We control ground truth. Every wallet has a known policy label. UMAP separation, anomaly recall, and clustering precision become measurable not anecdotal. Real Base data layers in on Saturday for credibility — but the pipeline must work without it.

## Policies

Each policy is a stochastic generator producing transactions for one wallet over a time window. Output rows match the Base schema in [05_data_plan.md](05_data_plan.md).

### `human_random`
- Inter-arrival: Exponential(λ = 1/(6h))  ≈ 4 tx/day
- Value: Lognormal(μ=4, σ=1.5) USD, clipped [1, 50_000]
- Counterparties: drawn from human-counterparty pool, repeat probability 0.3
- Time-of-day: rejection sample against a daytime-weighted curve (peaks 10-14, 19-22 local)
- Gas price: Normal(median_basefee, σ=10 gwei) — humans don't optimise
- Method: 60% native transfer, 30% ERC-20 transfer, 10% misc contract

### `agent_arb_deterministic`
- Inter-arrival: deterministic period 60–90s with ±5% jitter
- Value: tight band [50, 200] USD
- Counterparties: 2–3 fixed addresses (DEX router, token contract)
- Time-of-day: uniform 24h
- Gas price: median_basefee + Uniform(0, 1 gwei) — pathologically tight
- Method: same 4-byte selector >95% of calls

### `agent_payment_bot`
- Inter-arrival: bursty — Poisson cluster process. Burst arrivals Exponential(λ=1/4h); within burst Poisson(rate=10/min) for ~30s.
- Value: fixed payment amount with ±2% noise
- Counterparties: 1 per burst (recipient), drawn from a small pool of 20
- Time-of-day: skewed toward business hours but still mostly uniform
- Gas: tight, +20% over basefee for speed
- Method: ERC-20 transfer dominant

### `agent_compromised`
- Phase 1 (t < 8h): identical to `agent_payment_bot`
- Phase 2 (t ≥ 8h): drift behaviours
  - Counterparty pool replaced with new addresses (exfiltration target)
  - Value distribution shifts: rare large transfers (>10× normal) appear
  - Gas spikes: 5× burst-rate, gas price 3× normal
  - Method-id distribution adds a new selector (`approve` to malicious contract)

This is the **headline detection target**. The composite score should rise from low → critical across the drift.

### `collusion_ring`
- 5–10 wallets with shared coordinator
- Each wallet: light independent activity ~ `human_random`
- **Plus** coordinated bursts: every 2–4 hours, the ring trades at near-simultaneous timestamps (within 60s) on shared counterparty
- Detection target for the **clusterer**: these wallets cluster tightly; individually they look benign.

## API

```python
# src/ingest/synthetic.py
from src.ingest.synthetic import generate

txs, labels = generate(
    n_human=100,
    n_agent_arb=40,
    n_agent_payment=40,
    n_agent_compromised=10,
    n_collusion_rings=2,        # each = 5-10 wallets
    duration_hours=24,
    seed=42,
)
# txs: pd.DataFrame matching base schema
# labels: pd.DataFrame [addr, policy, role, ring_id]
```

## Quality bar

The synthetic data passes if:
1. UMAP on behavioural fingerprints visibly separates `human_random` vs. agent policies.
2. Composite scorer assigns critical/high to ≥80% of `agent_compromised` wallets after t=12h.
3. Clusterer recovers ≥80% of `collusion_ring` membership at silhouette ≥0.4.

These are the metrics on the demo slide.
