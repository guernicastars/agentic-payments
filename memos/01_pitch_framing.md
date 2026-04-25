# 01 — Pitch framing

**Date:** 2026-04-25

## The two-minute pitch (working draft)

> Visa, Mastercard, and Stripe Radar built fraud detection on a billion *human* transactions. They detect anomalies relative to a human behavioural baseline — geography, time-of-day, value bands. AI agents transact a thousand times more often, optimise gas to the wei, have no spatial pattern, and behave non-stationarily as the underlying models update. Existing fraud models are blind to them.
>
> We pulled 100,000 recent Base L2 transactions and built behavioural embeddings — here's the cluster plot. Agents and humans separate cleanly. Within the agent cluster, our anomaly detector flags compromised wallets the existing systems miss, and our interpretability layer gives a one-sentence reason for every flag.
>
> We're Bloomsbury Tech — a quantitative ML lab that publishes on causal inference and graph ML. **This is a statistical problem, not an LLM problem.** Stripe Radar can't ship this because they make money on agent transactions; Visa is on a 24-month release cycle; Sardine, Persona, Alloy were built for human-only data. We have an 18-month structural lead, and every month of agent traffic compounds our model.
>
> We start as the fraud signal layer for one mid-market PSP or acquirer. We expand into agent reputation scoring, AML for stablecoin flows, and dispute evidence generation. The eventual buyer is Stripe, Visa, Adyen, or Sardine — but by then we own the data.

## Four beats

1. **Precise gap.** Existing fraud models trained on human distributions; agents are structurally different.
2. **Demo evidence.** UMAP cluster plot + anomaly explanations on real(ish) Base data.
3. **Moat.** Statistical not LLM; data compounds; incumbents structurally slow.
4. **Expansion.** Fraud → reputation → AML → disputes → buyer is the network.

## Blomfield rubric (what he scores)

- Precise problem statement (no vision waffle)
- An *unusual* insight (the human-baseline fraud-model blindness)
- Evidence of velocity (working demo in 8 hours)
- Defensible moat (not LLM; data compounds; channel conflict for incumbents)
- Founder credibility (ICML-grade ML lab, not a vibe-coded MVP)

## Open framing decision

"Fraud detection" = easier pitch, smaller TAM. "Behavioural risk intelligence for agent traffic" = same product, bigger headroom (fraud, reputation, AML, disputes). **Default: pitch the broader frame, demo the fraud slice.** Blomfield watched Monzo go prepaid-card → full bank; he'll track the expansion arc.
