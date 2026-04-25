# 02 — Moat thesis

**Date:** 2026-04-25

## The three-property test

A defensible play in agentic payments must satisfy all three:

1. **Non-LLM ML.** Statistical / causal / graph methods that frontier labs don't optimise for. They default to fine-tuning a sequence model and lose on this class of problem.
2. **Compounding data asset.** Every agent-month of traffic scored makes replication harder. Stripe Radar took 8 years to be defensible because of this dynamic. Greenfield here.
3. **Vertical risk seat with channel conflict for incumbents.** Stripe Radar can't aggressively flag agent transactions — Stripe earns the take rate. Visa Decision Intelligence is on a 24-month release cycle. Anthropic is not a fraud company.

## Why "Apple Pay for agents" fails the test

- Thin UX layer; not non-LLM ML.
- No compounding data — every implementation is identical.
- Stripe / Apple / OpenAI ship it in two weeks.

## Why behavioural risk intelligence passes

- **Math:** non-stationary, sparse-label anomaly detection on graph-structured behavioural data with confounding. Causal inference + graph embeddings + interpretability is the right toolkit. Eugene's research lineage.
- **Data:** every agent-wallet-month scored becomes labelled training data. Adversarial agents adapt → weekly retrain → moat deepens.
- **Channel conflict:** Stripe takes 2.9% on agent volume; flagging it kills revenue. Visa Decision Intelligence ships quarterly. Sardine et al. trained on human DS; need to retool.

## Real competitors (not Anthropic, not Stripe)

Sardine, Alloy, Persona, ComplyAdvantage, Unit21, Hawk:AI. **None have agent-specific expertise yet.** That's the 12–18 month window.

## Why frontier labs lose this fight

LLMs are bad at non-stationary statistical anomaly detection on structured behavioural data with sparse labels and adversarial drift. The published evidence (across credit-card fraud, AML, market-manipulation detection) is consistent: fine-tuned sequence models underperform classical statistical + graph methods in this regime. Frontier teams default to "fine-tune transformer on transactions" and lose.

## Eventual buyer

Stripe / Visa / Adyen / Sardine. Acquisition is the right outcome — by the time it happens, we own the labelled-fraud dataset for the agent era.
