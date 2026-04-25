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
make demo
```

Equivalent explicit commands:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dash,dev]"
.venv/bin/python -m src.pipeline
.venv/bin/python -m streamlit run src/viz/dashboard.py
```

Use `.venv/bin/python -m streamlit` rather than `streamlit` so the shell does not need a global Streamlit command.
