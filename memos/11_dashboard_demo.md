# 11 — Dashboard demo

**Date:** 2026-04-25

## Product surface

Working name: **Agentic Payment Risk Console**.

The previous dashboard was visually interesting but under-explained: it led with a scatterplot before telling the viewer what decision the product helps them make. The Polymarket dashboard pattern is better: overview cards, tabbed tables, badges, factor bars, and ranked queues. The redesigned app follows that pattern.

Single-screen analyst console:
- Dataset switch: **Synthetic stress test**, **Dune x402 + baseline**, and **Public x402 Base**.
- Executive readout: one paragraph that says what the current data proves and what it does not prove.
- Metrics: transactions, wallets scored, immediate queue, watchlist, and either compromise recall or recipient count.
- Triage tab: alert queue with wallet, score, tier, action, policy, tx count, concentration, and explanation.
- Selected case: wallet evidence card plus factor breakdown.
- Behaviour Map tab: UMAP fingerprint space, deliberately secondary to the triage queue.
- Coordination tab: wallet graph and cluster table.
- Model Evidence tab: factor distribution so judges can see this is not an LLM vibes classifier.

## Demo beat

1. "This is a triage console for agentic payment risk."
2. Open on the Synthetic stress test. Show that deterministic agents, compromised drift, and collusion rings enter the queue while humans do not.
3. Read the selected case explanation out loud: timing, method concentration, counterparty concentration, coordination.
4. Switch to Dune x402 + baseline. Say: "This is the CTO pull: real x402 rows scored against ordinary Base traffic, with a snapshot trend table behind it."
5. Switch to Public x402 Base. Say: "On real public x402 traffic today, we see watchlist behaviour but no high-severity fraud claim yet. That honesty is the point."
6. Use the Coordination tab to make compromised-agent contagion concrete.

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
