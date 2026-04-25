# Agentic Payments — Behavioural Risk Intelligence for Agent Traffic

Bloomsbury Tech hackathon build (April 2026). Detects compromised, colluding, and adversarial AI agents on payment rails using behavioural fingerprinting + causal interpretability — the analytic stack the existing fraud incumbents (Stripe Radar, Visa DI, Sardine) don't have because they were trained on human distributions.

## Status

Hackathon prep day (Friday). Saturday: 10am–8pm build; 2-min pitch to Tom Blomfield (YC).

## Layout

```
agentic-payments/
├── memos/                # Build memos — see MEMOS.md for index
├── src/
│   ├── ingest/           # Data ingest: synthetic + Base/x402
│   ├── features/         # Behavioural fingerprint features
│   ├── models/           # Clustering + anomaly detection
│   └── viz/              # UMAP / dashboard figures
├── data/
│   ├── synthetic/        # Synthetic agent traffic (ground-truth labelled)
│   ├── raw/              # Raw chain dumps
│   └── processed/        # Feature tables
├── notebooks/
└── tests/
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dash,dev]"
python -m src.ingest.synthetic --n_agents 200 --n_humans 200 --hours 24 --out data/synthetic/run1.parquet
python -m src.features.fingerprint data/synthetic/run1.parquet -o data/processed/features.parquet
python -m src.models.score data/processed/features.parquet -o data/processed/scores.parquet
python -m src.viz.umap data/processed/features.parquet --labels data/synthetic/run1_labels.parquet
```

## Reused from adjacent repos

| From | What | Why |
|------|------|-----|
| `polymarket/pipeline/jobs/wallet_analyzer.py` | Pairwise wallet similarity + greedy clustering | Same shape — wallet, counterparty, side, timestamp |
| `polymarket/pipeline/jobs/insider_detector.py` | Z-score anomaly + coordination + composite suspicion 0-100 | Architecture lifts directly to agent traffic |
| `polymarket/network/embedding/` | Autoencoder + linear probing + Jacobian/correlation attribution | Interpretability layer for the "why was this flagged" answer |
| `dissertation/notes/cascade-network-analysis.md` | SIR-style infection model + branching-process bounds | Narrative spine for compromised-agent contagion |
