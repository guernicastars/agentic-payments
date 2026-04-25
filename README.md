# Agentic Payments — Behavioural Risk Intelligence for Automated Payment Traffic

Bloomsbury Tech hackathon build (April 2026). Detects compromised, colluding, and adversarial AI agents across payment rails using behavioural fingerprinting + causal interpretability. x402/Base is the first clean demo rail; the same actor-risk engine is intended to generalise to Stripe, Shopify, Visa/Mastercard authorization streams, PSPs, acquirers, and digital banks.

## Live web demo

Static Next.js port of the dashboard at `web/`. One-click deploy to Vercel:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fguernicastars%2Fagentic-payments&root-directory=web&project-name=agentic-payments&repository-name=agentic-payments)

Local: `cd web && npm install && npm run dev`. Data is pre-computed via
`python scripts/export_to_web.py` (no Python at runtime; the React
LiveTracker replays the recorded score stream at 1 tx/second).

## Status

Hackathon prep day (Friday). Saturday: 10am–8pm build; 2-min pitch to Tom Blomfield (YC).

## Layout

```
agentic-payments/
├── memos/                # Build memos — see MEMOS.md for index
├── scripts/              # Dune pulls, snapshot probes, analysis CLIs
├── src/
│   ├── ingest/           # synthetic.py, base.py, public_x402.py, facilitators.py
│   ├── features/         # Behavioural fingerprint features
│   ├── models/           # Clustering + anomaly detection
│   ├── viz/              # dashboard.py, embed.py, trend.py
│   ├── pipeline.py       # synthetic + --source <parquet> path
│   └── pipeline_public.py  # cooked-public-data pipeline
├── data/
│   ├── synthetic/        # Synthetic agent traffic (ground-truth labelled)
│   ├── raw/              # Raw chain dumps + Dune snapshot parquets
│   ├── samples/          # 50-100-row CSV seeds, committed for smoke tests
│   └── processed/        # Feature tables, real_x402_*.parquet
├── results/
│   ├── figures/          # trend.png, headline.png, real_umap.png (committed)
│   └── tables/           # snapshot_summary.csv
└── tests/
```

## Quick start

```bash
make demo               # synthetic pipeline + Streamlit dashboard
make public             # public-x402 (Blockscout, no API key) pipeline
```

If `make` is not available:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dash,dev]"
.venv/bin/python -m src.pipeline                          # synthetic
.venv/bin/python -m src.pipeline_public --refresh         # public x402 (live fetch)
.venv/bin/python -m streamlit run src/viz/dashboard.py
```

The dashboard has a **Dataset** segmented control that switches between
`Synthetic stress test`, `Dune x402 + baseline` (CTO Dune pull cooked
through the same pipeline as a real-data bridge), and `Public x402 Base`.
Tabs:

- **Live Tracker** — replay-based live fraud stream (1 tx/s), uses
  `@st.fragment(run_every="1s")`. Clears warm-up at ~30 wallets and emits
  alerts when a wallet's behavioural composite enters the top-8% of the
  live population. Code: `src/live/tracker.py`.
- **Triage / Behaviour Map / Coordination / Model Evidence** — static
  views over the cooked dataset.
- **12-month Trend** — aggregates the four Dune snapshot parquets at
  `data/raw/x402_snapshot_*.parquet` (falls back to locked numbers from
  memo 16 if those files aren't present yet).

Pipeline on a pre-ingested real-data parquet:

```bash
.venv/bin/python -m src.pipeline --source data/raw/base_ingested.parquet
```

CTO/Dune x402 traffic + Base baseline:

```bash
make dune
```

Manual synthetic pipeline:

```bash
.venv/bin/python -m src.ingest.synthetic --n_human 100 --n_agent_arb 40 --n_agent_payment 40 --n_agent_compromised 10 --hours 24 --out data/synthetic/run1.parquet
.venv/bin/python -m src.features.fingerprint data/synthetic/run1.parquet -o data/processed/features.parquet
.venv/bin/python -m src.models.cluster data/synthetic/run1.parquet
.venv/bin/python -m src.models.score data/processed/features.parquet -o data/processed/scores.parquet
.venv/bin/python -m src.viz.embed data/processed/features.parquet --labels data/synthetic/run1_labels.parquet --scores data/processed/scores.parquet
```

## Demo dashboard

The Streamlit app is the hackathon demo surface: UMAP wallet clusters,
composite risk tiers, top wallet explanations, a coordination graph, and a
12-month behaviour trend. It includes synthetic stress-test data, CTO/Dune
x402 traffic scored against an ordinary Base baseline, and the public
x402/Base overlay. It auto-builds synthetic demo artifacts if
`data/processed/embedding.parquet` is missing.

## Reused from adjacent repos

| From | What | Why |
|------|------|-----|
| `polymarket/pipeline/jobs/wallet_analyzer.py` | Pairwise wallet similarity + greedy clustering | Same shape — wallet, counterparty, side, timestamp |
| `polymarket/pipeline/jobs/insider_detector.py` | Z-score anomaly + coordination + composite suspicion 0-100 | Architecture lifts directly to agent traffic |
| `polymarket/network/embedding/` | Autoencoder + linear probing + Jacobian/correlation attribution | Interpretability layer for the "why was this flagged" answer |
| `dissertation/notes/cascade-network-analysis.md` | SIR-style infection model + branching-process bounds | Narrative spine for compromised-agent contagion |
| `x402.watch` + Base Blockscout API | Live x402 facilitator → EIP-3009 settlement decoder | Real demo data without Dune/Etherscan API keys |
| Dune `base.transactions` (4 historical snapshots) | Jun 2025 / Oct 2025 / Jan 2026 / Apr 2026 trend | 12-month behaviour shift: 28,000× volume, 100× median tx compression |
