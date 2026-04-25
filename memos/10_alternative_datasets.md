# 10 — Alternative datasets

**Date:** 2026-04-25

Purpose: keep the demo robust if x402/Base volume is thin, if Coinbase data lands late, or if we need a second validation frame.

## Priority A — closest to the hackathon claim

1. **Base + x402 facilitator settlements**
   - Source: Coinbase x402 facilitator docs and Base x402 seller docs.
   - Why: closest behavioural distribution to agentic payments; supports the pitch directly.
   - Label plan: known facilitator / x402 settlement addresses as agent-positive; sampled Base EOAs as human baseline; merchants/receivers as counterparty features, not labels.
   - Risk: exact facilitator on-chain address discovery may need x402.watch / explorer validation.
   - Links: https://docs.cdp.coinbase.com/x402/core-concepts/facilitator, https://docs.base.org/ai-agents/payments/accepting-payments

2. **Base / Ethereum public chain history**
   - Source: Google Cloud Blockchain Analytics / BigQuery public blockchain tables, plus explorer exports where needed.
   - Why: broad human + bot transaction baseline, useful for calibrating gas, timing, and counterparty distributions.
   - Label plan: unlabeled baseline only; combine with known contract categories (DEX routers, bridges, stablecoin contracts).
   - Risk: Base availability/table names need confirmation in the active Google dataset; Ethereum is stable but less agentic-payment-specific.
   - Links: https://docs.cloud.google.com/blockchain-analytics/docs/dataset-ethereum, https://cloud.google.com/blog/products/data-analytics/data-for-11-more-blockchains-in-bigquery-public-datasets

3. **Forta alerts as weak labels**
   - Source: Forta alert API / ML resources.
   - Why: converts real security detections into weak positive labels for compromised/drifted wallets.
   - Label plan: wallets appearing in critical/high confidence exploit, phishing, approval-drain, or anomalous-transfer alerts become weak-positive; chain baseline remains weak-negative.
   - Risk: alert taxonomy may not map cleanly to "agent compromise"; use as security validation, not primary agent/human split.
   - Links: https://docs.forta.network/en/latest/network-overview/, https://docs.forta.network/en/latest/ml-data-resources/

## Priority B — good for graph/fraud validation

4. **Elliptic Bitcoin dataset**
   - Source: Elliptic / Kaggle public labeled Bitcoin transaction graph.
   - Why: canonical licit/illicit crypto graph benchmark; lets us show the model family ports to AML.
   - Label plan: illicit vs licit graph labels; ignore agent-specific features, keep temporal/counterparty/graph features.
   - Risk: Bitcoin UTXO semantics differ from Base account model, so this validates graph-risk muscle, not agentic payment rails.
   - Links: https://www.kaggle.com/datasets/ellipticco/elliptic-data-set/data, https://www.elliptic.co/blog/elliptic-dataset-cryptocurrency-financial-crime

5. **Elliptic++ / Elliptic2 research datasets**
   - Source: published temporal graph extensions.
   - Why: stronger graph structure and wallet/address interactions than original Elliptic; useful after the hackathon.
   - Label plan: illicit address / subgraph labels.
   - Risk: may require request/download work; not a Friday-night dependency.
   - Links: https://arxiv.org/abs/2306.06108, https://arxiv.org/abs/2404.19109

6. **Address poisoning / phishing datasets**
   - Source: CMU / USENIX-style address-poisoning studies and Ethereum phishing datasets.
   - Why: directly resembles compromised-agent and adversarial-counterparty behaviours.
   - Label plan: known phishing/poisoning txs as adversarial positives; normal transfers as baseline.
   - Risk: dataset access may be slower than using Forta weak labels.
   - Links: https://www.cylab.cmu.edu/news/2026/01/07-blockchain-address-poisoning.html, https://arxiv.org/abs/2409.02386

## Priority C — useful only for storytelling / baseline ML

7. **European credit-card fraud dataset**
   - Source: Kaggle two-day anonymised card transactions.
   - Why: classic fraud baseline with extreme class imbalance; useful for a slide explaining why old fraud datasets are the wrong distribution.
   - Label plan: fraud class as positive; do not use for wallet graph claims.
   - Risk: PCA-anonymised features mean no behavioural interpretability; not agentic or on-chain.
   - Link: https://www.kaggle.com/datasets/ghnshymsaini/credit-card-fraud-detection-dataset

8. **Internal/synthetic transaction policies**
   - Source: our generator.
   - Why: controlled ground truth for deterministic agents, payment bots, compromised drift, and collusion rings.
   - Label plan: exact policy labels.
   - Risk: must be framed honestly as synthetic validation; combine with at least one real chain slice for credibility.

## Recommended Saturday sequence

1. Keep the synthetic generator as the ground-truth demo path.
2. Pull Base/x402 settlements first; if identifiable volume is usable, run the same feature/scoring pipeline and show it as "real traffic overlay".
3. If x402 is thin, pull Forta security alerts on Base/Ethereum for compromised-wallet validation.
4. Mention Elliptic only as the longer-term AML expansion path.
