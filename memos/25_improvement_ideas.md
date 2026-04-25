# 25 — Improvement ideas

**Date:** 2026-04-25

## Ranked gaps (week-1 post-pitch unless noted)

1. **Wire real fraud labels.** Facilitator-address = "agent" is self-identifying, not fraud. Join Forta alert addresses (compromise-positive) and Chainalysis sanctions list into ingestion. Memo 00 Q&A already promises this; ship it.

2. **Coordination/collusion graph — name the rings.** Louvain community detection on wallet co-occurrence graph. Demo surfaces *named coordinated rings*, not single anomalous wallets.

3. **Adversarial-agent demo.** Memo 03 flags as strongest moat angle (B+) but no live demo. Synthetic evader: randomised inter-arrival, loosened gas tightness, jittered timing. Show detector still flags. Only Saturday-eligible item if rehearsal #1 finishes early — capped at 30 min, revertable.

4. **Counterfactual explanation.** Replace correlational factor bars with: "if this wallet behaved like its nearest non-flagged peer, score 92 → 34." Earns the word "causal" in the moat thesis.

5. **Widen snapshot windows.** Current 1h × 24 extrapolation (151–400 tx) is checkable on Dune. Either pull full-day windows or reframe headline as "peak hour."

---

## Add below
