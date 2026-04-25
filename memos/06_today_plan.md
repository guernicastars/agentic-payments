# 06 — Today's plan (Friday 2026-04-25)

> **Status: completed Friday evening.** All Friday blocks shipped (synthetic pipeline, features, clusters, scores, UMAP, dashboard). For Saturday actuals see memos 12 (live x402 track), 15 (Dune snapshots track), 16 (locked numbers), and 17 (data quality).

## Goal

End the day with a working **synthetic-data pipeline** end-to-end (generator → features → clusters → composite scores → UMAP figure). Saturday is then "swap synthetic for real data + train interpretability probe + Streamlit + rehearse."

## Hour-by-hour

| Time | Block | Output |
|------|-------|--------|
| Now → +1h | Scaffold + memos | `memos/`, dir layout, `pyproject.toml`, README, initial commit |
| +1h → +2h | Synthetic generator | `src/ingest/synthetic.py` + 5 policies; tested 200 wallets × 24h |
| +2h → +4h | Feature engineering | `src/features/fingerprint.py` — 30-50 features per wallet |
| +4h → +5h | Port clusterer | `src/models/cluster.py` from `wallet_analyzer.py` |
| +5h → +6h | Port composite scorer | `src/models/score.py` from `insider_detector.py` |
| +6h → +7h | UMAP + headline figure | `src/viz/umap.py` → `results/figures/headline.png` |
| +7h → +8h | Smoke test + memos refresh | End-to-end run; what worked, what to fix Saturday |
| 7pm | Friday rooftop reception | Network. Don't talk too much shop; signal credibility, find gaps in our pitch by listening |

## Saturday handoff

Saturday morning the cofounder arrives with Coinbase data. Plan:

| Time | Block |
|------|-------|
| 10:00 → 10:30 | Confirm data format, ingest into our schema |
| 10:30 → 12:00 | Re-run features + cluster + score on real data |
| 12:00 → 14:00 | Linear probe + interpretability (port from `polymarket/network/embedding/`) |
| 14:00 → 16:00 | Streamlit single-screen dashboard (cluster left, anomaly list right with explanations) |
| 16:00 → 17:30 | Pitch rehearsal × 5; tighten to exactly 2 minutes |
| 17:30 → 19:00 | Buffer / polish |
| 19:00 → 20:00 | Pitch slot + Q&A |

## Risks

- **Real data thin or unavailable:** synthetic carries the demo; we frame as "validated on 5 ground-truth-labelled policy classes; same pipeline runs on Base."
- **Interpretability probe doesn't converge in time:** the composite-score "explanations" come from feature-attribution rules (top-3 z-scores per flagged wallet), no probe needed for the demo.
- **UMAP separation muddier than expected:** keep the t-SNE fallback ready; tune perplexity; if both fail, switch to PCA + isolation-forest on raw features.
