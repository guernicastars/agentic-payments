# 03 — Open gaps in agentic payments

**Date:** 2026-04-25

Compact list of unsolved problems by layer. Moat profile: **B** = good for Bloomsbury; M = mid; X = bad / commoditising.

## Identity & delegation
- Persistent agent identity across protocols — no Layer 0 — **M** (standards battle, hyperscaler-owned)
- Cryptographic delegation chains across A→B→C calls — **X** (PKI plumbing; Entrust et al. own it)
- Portable agent reputation across platforms — **B** (behavioural angle, our wedge)
- Distinguishing legitimate from malicious automated traffic — **B**

## Trust & authorisation
- Mandate scope verification (was the action within user intent?) — **B**
- Multi-step intent reconstruction — M
- Real-time policy compliance enforcement — X (symbolic, low ML moat)

## Risk & fraud — our cluster
- Fraud detection on agent behavioural distributions — **B (strong)**
- Rogue vs. compromised vs. malicious agent classification — **B**
- Anomaly detection without human baselines — **B**
- Adversarial agent detection (agents that game scoring systems) — **B (very strong)** — causal-interp work is literal SOTA here
- Coordinated multi-agent fraud / collusion / laundering — **B** — graph ML directly applies

## Disputes & liability
- Causal liability attribution under ambiguous intent — B (harder demo)
- Evidence synthesis for agent disputes — M
- Chargeback pricing for agent transactions — M

## Settlement
- Cross-rail routing optimisation — M (bandit; others can do)
- Stablecoin / fiat hybrid orchestration — X (Crossmint, Privy)
- International FX optimisation — X

## Observability & compliance
- Audit trail synthesis at machine speed — X
- AML / sanctions screening for agent flows — M (regulated, slow)
- Causal explanation of flagged transactions — **B**

## Commerce-specific
- Counterparty legitimacy verification — M
- Negotiation protocol standardisation — X (standards battle)

## What we collapse to

The B cluster is one product: **behavioural risk intelligence layer for agent traffic**. Fraud is the wedge. Reputation, dispute evidence, AML, adversarial detection all sit downstream as the data asset compounds.
