# 12 — Public data collection

**Date:** 2026-04-25

## Easy-ish data collected

No API keys needed.

1. **x402.watch facilitator directory**
   - Collected into `data/raw/x402_facilitators.parquet`.
   - Tracked sample: `data/raw/sample_x402_facilitators.csv`.
   - Use: facilitator URL list, public metadata, quick target list for `/supported` probes.
   - Source: https://www.x402.watch/facilitators

2. **Coinbase x402 facilitator addresses**
   - Collected into `data/raw/x402_addresses.parquet`.
   - Tracked sample: `data/raw/sample_x402_addresses.csv`.
   - Use: Coinbase address watchlist for Base Blockscout queries.
   - Source: https://x402.watch/facilitator/coinbase

3. **OpenX402 `/supported` endpoint**
   - Collected into `data/raw/x402_supported_probe.parquet`.
   - Found active Base signer `0x97316FA4730BC7d3B295234F8e4D04a0a4C093e8` and Base USDC asset `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`.
   - Source: https://facilitator.openx402.ai/supported

4. **Base Blockscout no-key txlist**
   - Collected into `data/raw/base_facilitator_txlist.parquet`.
   - Normalized into `data/processed/real_x402_base.parquet`.
   - Cooked payment-only rows into `data/processed/real_x402_payments.parquet`.
   - Tracked samples:
     - `data/processed/sample_real_x402_base.csv`
     - `data/processed/sample_real_x402_payments.csv`
     - `data/processed/sample_real_x402_scores.csv`
   - Source: https://base.blockscout.com/api

## Current pull summary

At first pull:
- 7,512 Base facilitator-address transactions.
- 437 decoded x402/EIP-3009 USDC payment rows.
- 116 unique payer wallets.
- 19 unique recipient wallets.
- 116 payer wallets cooked through the scorer: 65 medium, 51 low, 0 high.

We decode `0xe3ee160e` calls to Base USDC as EIP-3009-style `transferWithAuthorization` rows:
- payer address
- recipient address
- USDC amount
- validity window
- authorization nonce
- facilitator/signer address

This is the first real-data overlay for the synthetic demo.

Committed artifacts for cofounder access:
- `data/raw/x402_facilitators.parquet`
- `data/raw/x402_addresses.parquet`
- `data/raw/x402_supported_probe.parquet`
- `data/processed/real_x402_base.parquet`
- `data/processed/real_x402_payments.parquet`
- `data/processed/real_x402_features.parquet`
- `data/processed/real_x402_scores.parquet`
- `data/processed/real_x402_embedding.parquet`

The larger raw Blockscout txlist remains ignored and reproducible via `python -m src.ingest.public_x402`.

## Commands

```bash
python -m src.ingest.public_x402
python -m src.pipeline_public
```

`src.ingest.public_x402` fetches and normalizes public data. `src.pipeline_public` cooks it through the same feature/scoring/embedding stack used for the synthetic demo.

## Not easy today / cofounder queue

1. **Dune x402 dashboards**
   - Likely useful for volume and aggregate trend, but requires either manual dashboard export or Dune API key.

2. **BigQuery Blockchain Analytics**
   - Good for broader Base/Ethereum baseline, but requires GCP auth/project setup and table-name confirmation.

3. **BaseScan / Etherscan v2**
   - Easy technically, but needs API key for stable higher-volume pulls.

4. **Forta alerts**
   - Good weak labels for compromised/exploit wallets, but needs alert taxonomy work before cooking.

5. **x402scan internal API**
   - Public page is visible, but easy API endpoint was not obvious from a quick probe. Worth inspecting in browser/devtools if more x402-specific history is needed.
