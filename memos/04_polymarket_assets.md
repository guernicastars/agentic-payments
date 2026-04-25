# 04 — Polymarket assets we lift

**Date:** 2026-04-25

## High-leverage code (port directly)

### `polymarket/pipeline/jobs/wallet_analyzer.py` (372 LOC)
Pairwise wallet similarity from `wallet_activity` (24h window):
- Timing correlation (5-min buckets)
- Market overlap (Jaccard on condition_ids)
- Direction agreement (BUY/SELL alignment)
- Greedy clustering: edge if `similarity > CLUSTER_MIN_SIMILARITY` and `overlap > CLUSTER_MIN_OVERLAP`

**Port:** replace `condition_id` with `(to_address, method_id)` tuple; replace `side` with `value_bucket`; everything else lifts. Output → `agent_clusters` table (or DataFrame for hackathon).

### `polymarket/pipeline/jobs/insider_detector.py` (901 LOC)
Five detection methods + composite scoring:
1. **Pre-news trading** — trades preceding major events (skip for agents; replace with pre-known-exploit timing)
2. **Statistical anomaly** — z-scores on per-trader metrics (trade frequency, avg size, win rate, market entropy)
3. **Profitability outliers** — risk-adjusted returns (skip for agents v1)
4. **Coordinated trading** — wallet groups acting within 5-min window with shared market overlap
5. **Composite suspicion** — weighted 0–100 score with tiers: critical (≥75), high (≥50), medium (≥25), low

**Port:** drop methods 1+3 (no analog yet), keep 2+4, swap features for behavioural fingerprint, keep tiering + composite score architecture verbatim.

### `polymarket/pipeline/jobs/signal_compositor.py` (380 LOC)
8-factor weighted composite (OBI, volume anomaly, large-trade bias, momentum, smart money, concentration, arbitrage, insider). Weights normalised to [-100, +100], clamp at end.

**Port:** template. Replace 8 polymarket factors with 8 agent-specific risk factors:
1. Inter-arrival entropy anomaly
2. Gas-tightness anomaly
3. Counterparty diversity anomaly
4. Time-of-day uniformity anomaly
5. Cluster co-membership (from clusterer)
6. Method-call burstiness
7. Value-distribution entropy
8. Failed-transaction ratio

## Heavier reuse if time permits

### `polymarket/network/embedding/` (4,009 LOC)
- `model.py` — autoencoder (32-dim bottleneck on 27 features); same shape works for our 30–50 agent features
- `probes.py` — linear probes with stratified-CV + permutation tests (1,000 perms, p<0.005)
- `interpret.py` — correlation + Jacobian attribution; "this direction = high-frequency low-value optimisation"
- `train.py` — full training loop

**Demo value:** instead of "we flagged this agent", we say "we flagged this agent, and the 3 highest-attribution dimensions are gas-optimisation tightness, counterparty diversity collapse, and time-of-day uniformity — consistent with a compromised arbitrage agent." That sentence wins the pitch.

### `polymarket/network/signals/cascade.py` (155 LOC)
Cascade signal detection. Pairs with dissertation cascade-network-analysis.md.

### `polymarket/network/gnn/` (graph_builder.py + model.py + online_learner.py)
GNN over wallet-counterparty graph. Stretch goal Saturday afternoon.

## Theoretical / narrative

### `dissertation/notes/cascade-network-analysis.md`
SIR-style infection model on agent network with branching-process bounds + spectral vulnerability theorem. **Use one slide:** "When a compromised agent transacts with N others at infection probability p, the cascade goes critical above p·N > 1. We detect the precursors before criticality." This single slide differentiates us from every other team.

### `polymarket/Embedding_Interpretability_Paper.tex` (Eugene, Feb 2026)
Already-written published-grade interpretability methodology. Cite in pitch as credibility signal.

## Things NOT to lift

- ClickHouse infrastructure — too heavy for hackathon. Use parquet + DuckDB if needed.
- Polymarket-specific signals (OBI, arbitrage scanner) — domain-mismatched.
- Discord bot, dashboards — distraction.
