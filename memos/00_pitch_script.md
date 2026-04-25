# 00 — Pitch script (2 minutes, beat-by-beat)

**Date:** 2026-04-25 · For Saturday rehearsal with stopwatch.

Total budget: 120s + 15s buffer. Each beat is timed; rehearse with timer until reliably ±2s.

---

## [0:00 → 0:20] BEAT 1 — Precise gap (20s)

> "Visa, Mastercard, Stripe Radar — every fraud system in production was trained on a billion *human* transactions. Median ticket size $30 to $100, browser fingerprints, time-of-day patterns, geographic priors.
>
> AI agents on stablecoin rails behave nothing like that. We pulled the data: median x402 transaction is **one tenth of a cent**. Existing fraud models can't even represent these as features. Agent traffic is invisible to them — not anomalous, *invisible*."

**Cue:** open dashboard on `Public x402 Base` source, no need to point at chart yet.

---

## [0:20 → 0:55] BEAT 2 — Demo evidence (35s)

Open the **Behaviour Map** tab. UMAP visible.

> "We pulled real x402 settlements off Base in the last week — 1,000-plus transactions through known facilitators, decoded the EIP-3009 signers, computed a 36-feature behavioural fingerprint per wallet. Agents and humans separate cleanly here." *(point at clusters)*

Switch to **Triage** tab. Pick one critical-tier wallet.

> "Pick a flag. The system explains the wallet in one sentence: timing CV, gas tightness, counterparty concentration, late drift, peer coordination. This isn't black-box LLM — every score traces to an observable behavioural signal." *(point at factor bars)*

Switch to **12-month Trend** tab.

> "And it's accelerating. Jun 2025 to today: agent population up 40 percent, median transaction shrunk **100×**, daily volume up **28,000×**. Quarterly retraining cycles cannot keep up."

---

## [0:55 → 1:30] BEAT 3 — Moat (35s)

> "Three reasons we can ship this and incumbents can't.
>
> One. **Statistical, not LLM.** This is a graph and time-series problem. Our team publishes ICML-grade ML on causal inference and graph learning. We have an 18-month structural lead — Sardine, Persona, Alloy are built for human-only data, they'd need to throw away their training set.
>
> Two. **Data compounds.** Every month of agent traffic narrows our prior; incumbents see only their slice of merchants.
>
> Three. **Channel conflict.** Stripe Radar can't ship this — Stripe earns interchange on agent transactions. Visa moves on a 24-month release cycle. The market opens between now and when Adyen or Stripe acquire whoever's furthest along."

---

## [1:30 → 1:55] BEAT 4 — Expansion (25s)

> "We start as the fraud signal layer for one mid-market PSP or acquirer — that's the wedge. We expand into agent reputation scoring, AML for stablecoin flows, dispute evidence generation. By the time Stripe or Visa acquires, we own the dataset they need."

---

## [1:55 → 2:00] BEAT 5 — Close (5s)

> "Bloomsbury Tech. Behavioural risk intelligence for agentic payments."

---

## Buffer (15s)

If under time, optionally add at end of beat 2:
> "And it ports — same pipeline runs on Stripe authorization streams, Shopify checkout events, card-not-present rails. See memo 14 for the generalisation."

---

## Pre-delivery checklist (T-5 minutes)

- [ ] Streamlit running on `make demo`, `Public x402 Base` selected
- [ ] Browser zoom 110% so back-row can read
- [ ] Timer visible (phone, not laptop)
- [ ] `results/figures/trend.png` open in second tab as backup
- [ ] Memo 13 PDF (methodology) open as backup if pressed on rigour
- [ ] Speaker glass of water; backup speaker briefed on beat 2
- [ ] One-line memorised opener if mic glitches: "AI agents transact at a thousandth of a cent — Visa's models can't even see them."

## Q&A predictions and 30-second answers

| Likely question | Answer beat |
|---|---|
| "How is this different from Sardine?" | Sardine trains on human-device + behavioural signals. Throwing away their training set on agent rails is structurally hard. We build only on agent-shaped distributions from day one. |
| "What's your label source?" | Weak supervision: x402 settlements as agent-positive, Forta alert addresses as compromise-positive, sampled non-x402 EOAs as human baseline. Strong labels follow customer integration. |
| "Stripe could just do this." | They earn interchange on agent traffic. They will license it before they build it — see channel conflict argument. |
| "Why not Polygon / Solana?" | Base + x402 has the cleanest agent-positive label today. Architecture ports — same pairwise wallet similarity ran on Polymarket Polygon last quarter (memo 04). |
| "Bipartite oddity in Oct 2025?" | One merchant captured 99.98% of volume. Excluded as a transitional pilot, not a trend. Detecting that distortion in 30 seconds is part of what we ship — see memo 17. |

## Post-pitch follow-up (if Blomfield hands a card)

Immediate (within 4 hours):
- One-page deck PDF: trend slide + UMAP screenshot + moat bullets
- Methodology memo PDF link (`memos/13_methodology_memo.pdf`)
- Repo invite to `guernicastars/agentic-payments`
