# 11 — Dashboard demo

**Date:** 2026-04-25

## Product surface

Working name: **Agentic Payment Risk**.

Single-screen Streamlit app:
- Top row: transaction count, wallet count, high-risk count, compromise recall, human false-high count.
- Main visual: 2D behavioural embedding. Colour by risk tier for the pitch; flip to policy only if judges ask how we know the synthetic ground truth.
- Right rail: risk tier histogram + top suspicious wallets table.
- Bottom left: wallet inspector with one-line explanation and factor breakdown.
- Bottom right: coordination graph from pairwise wallet similarity.

## Demo beat

1. "This is not a toy fraud classifier; it is a behavioural risk layer."
2. Show humans and agents separating in the embedding.
3. Click a compromised or colluding wallet and read the explanation out loud: timing drift, gas tightness, counterparty concentration, coordination.
4. Show the coordination graph to make "agent networks fail as networks" tangible.
5. Say the next step is replacing synthetic labels with Base/x402 settlements and Forta weak labels.

## Dashboard commands

```bash
python -m src.pipeline
streamlit run src/viz/dashboard.py
```

Fresh clones can skip the first command; the dashboard auto-builds synthetic artifacts if they are missing.
