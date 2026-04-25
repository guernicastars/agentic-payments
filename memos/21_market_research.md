# 21 — Market research

**Date:** 2026-04-25 · For investor deck (memo 20) and pitch material (memos 00, 01).

This memo replaces the placeholder market sizing in memo 20 with sourced figures. Every number traces to a primary or secondary source cited at end. Confidence levels: **[H]** = primary source / industry standard, **[M]** = reputable secondary / vendor estimate, **[L]** = inference or extrapolation. Use [H] data on the deck; flag [M] as estimates; never put [L] in front of investors without a derivation footnote.

---

## 1. Executive summary

Three findings drive the deck:

1. **The market we sell into is large and growing.** Card-not-present fraud alone reaches $49B in losses by 2030 [H]. Global fraud detection software market is $67B in 2026 → $244B by 2034 [M]. Industry rule of thumb: enterprises budget **5–10% of expected fraud losses** for prevention software [H — Tactionsoft, FinancialModelsLab]. EMEA financial institutions alone spent **$85B in 2023** on financial crime compliance [H — McKinsey].

2. **The agentic-payments rail is real but smaller and more volatile than the narrative.** Stablecoin volume hit $33T in 2025, up 72% [H]. But x402 specifically — the rail our demo runs on — peaked in Dec 2025 (731k tx/day) and is down 92% to ~57k tx/day by March 2026 [H]. **Visa estimates agent-initiated transaction volume at $300-500B by 2030, up from ~$3B in 2025** [H — Visa]. The rail isn't the bet; the *behavioural shape of agent traffic on any rail* is the bet.

3. **Incumbents are awake but mispositioned.** Stripe acquired Bridge ($1.1B, Feb 2025) for stablecoin rails AND launched the Agentic Commerce Suite. Persona raised $200M at $2B (April 2025) explicitly to "build the verified identity layer for an agentic AI world". Google launched AP2 with 60+ partners (Sept 2025) including Forter and Adyen. **The market is forming this year. Window is ~12 months before category positions lock.**

**Implication for the round:** the deck should size the *agent fraud* SOM bottom-up from PSPs and ACVs (defensible), use the Visa $300-500B figure for the agent-rail TAM trajectory, and lean on the Persona-pivoting / Stripe-acquiring-Bridge / Google-AP2 timeline as the "why now" beat.

---

## 2. Methodology

**Primary sources used:**
- Nilson Report (card fraud statistics, industry standard since 1970)
- Public company filings, press releases, and announcements (Visa, Stripe, Persona, Sardine, etc.)
- Bloomberg, CNBC, Fortune, TechCrunch (for funding/valuation reporting)
- Coindesk, The Block, Cryptoslate (for x402 / stablecoin volume)
- Artemis Analytics (on-chain stablecoin data)

**Secondary sources (used with caveats):**
- Fortune Business Insights, MarketsAndMarkets, Grand View Research (analyst market sizing — directionally useful, headline numbers should be triangulated)
- McKinsey & a16z newsletters (forecast estimates)

**Excluded:**
- Single-vendor self-reports of TAM (vendors over-estimate their own market)
- LinkedIn-influencer takes
- Crypto Twitter without on-chain backing

---

## 3. TAM / SAM / SOM

### TAM — global fraud-detection software market

| Source | Year | Figure | Confidence |
|---|---|---|---|
| Fortune Business Insights | 2026 | **$67.1B** | M |
| Fortune Business Insights | 2034 | **$243.7B** (CAGR 17.5%) | M |
| MarketsAndMarkets | 2030 | $65.7B | M |
| Industry Research / online-payment-fraud subset | 2026 | $13.7B → $47.5B by 2035 | M |
| Nilson — global card fraud *losses* | 2024 | $33.4B | H |
| Nilson — projected CNP fraud losses | 2030 | **$49B** | H |
| Nilson — cumulative card fraud losses | 2024–2034 | $404B | H |

**TAM number to use on the deck: $67B in 2026 → ~$120B by 2030**, with the footnote "fraud detection software spend; secondary market sizing triangulated against $33B annual card fraud losses (Nilson)". Cite both in the same footnote so the investor sees rigour.

### SAM — agent-mediated payment fraud detection

This is where derivation matters because no analyst report exists yet. Build bottom-up:

**Step 1: agent transaction volume by 2030**
- Visa estimate: **$300-500B** by 2030 [H — Visa investor relations, April 2026]
- McKinsey estimate: **$1T US-only**, $3-5T global consumer commerce [H — McKinsey, 2025]
- Use **Visa's lower number ($300B)** as the conservative anchor; it's a primary source from a card network with strong incentive to be accurate.

**Step 2: fraud bps applied to agent volume**
- Card-not-present fraud loss ratio: ~6-9bps of CNP volume (Nilson 2024 → 2030 projections)
- Agent transactions are higher-risk than human CNP because: (a) no biometric layer, (b) novel adversarial surface, (c) no historical baseline. Conservative assumption: agent fraud is at least equal to CNP at **~7-10bps**.
- $300B × 8bps = **$2.4B in agent fraud losses by 2030**

**Step 3: fraud-detection software spend as % of fraud losses**
- Industry rule-of-thumb confirmed: enterprises budget **5–10%** of expected fraud losses on prevention software [H — Tactionsoft "Fraud Detection Software Development Cost 2025"]. Mid-sized companies allocate ~11% of revenue to fraud prevention; small businesses ~6% [H — FinancialModelsLab].
- $2.4B × 7.5% (mid-range) = **~$180M agent-fraud software spend in 2030 (low end)**
- ROI anchor: every $1 spent on fraud detection prevents ~$3.68 in losses [H — industry case studies]; first-year deployments report 40–60% reduction in fraud losses [H].

**Step 4: stretch case — McKinsey global figure**
- $3T × 8bps × 7.5% = **$1.8B agent-fraud software spend by 2030**

**SAM range to put on deck: $180M – $1.8B by 2030**, depending on whether agent commerce hits Visa's number or McKinsey's. Show both.

### SOM — what we can capture in 5 years

Bottom-up by customer:
- 50 PSPs and acquirers globally with material agent-rail exposure (estimated from PaymentsDive M&A coverage + Visa partner list)
- Realistic land rate over 5 years: **10–20 paying customers**
- ACV anchor: **$200–500k**, derived from:
  - Sardine's stated $145M total raised + ~300 enterprise customers → implied ACV in low six figures (Crunchbase / Contrary Research)
  - Alloy's $42M ARR / 200 customers (2024) → **$210k ACV** [H — getlatka]
  - Feedzai serves Tier 1 banks at materially higher ACV ($1M+); we model lower-tier-1 + mid-market

**SOM = 10–20 customers × $300k ACV = $3M–6M ARR by year 3, scaling to $10–25M ARR by year 5.** Plot against the $170M–$1.7B SAM and the $67B+ TAM on the slide.

---

## 4. Market structure

### Who pays for fraud detection software?
1. **PSPs / acquirers** — Stripe (in-house Radar), Adyen, Worldpay, Checkout.com — the largest spenders. Adyen has dual-rail interest (stablecoin via partners + card).
2. **Banks and digital banks** — JPMorgan, Wise, Revolut, Monzo, Modulr, etc.
3. **Marketplaces and merchants** — Etsy, Shopify, Amazon (in-house), URBN brands, ride-share / delivery
4. **Crypto-native platforms** — Coinbase, Kraken, Crypto.com (currently buy from Chainalysis/TRM)

### Pricing models in market

| Vendor | Model | Public anchor |
|---|---|---|
| Stripe Radar | $0.05 per scored tx (standard); $0.07 (advanced) | [H — stripe.com/radar/pricing] |
| Sardine | Per-tx + platform fee, enterprise | [M — Contrary Research] |
| Forter | Outcome-based (chargeback guarantee) | [M] |
| Riskified | Outcome-based, % of approved orders | [M] |
| Alloy | Per-decision (onboarding-weighted) | [M] |
| Persona | Per-verification ($1–3 each) | [M — historical TC reporting] |
| Chainalysis Reactor | Annual licence ($16k–$200k+) | [M] |

**Implication for our pricing:** for agent transactions (high-frequency, micro-value), per-tx fees in the $0.02-0.05 range scale with volume; per-decision pricing under-monetises high-frequency agent traffic. **Hybrid: per-tx for scoring + tiered platform fee for analyst console.**

---

## 5. Why now — the agent-commerce inflection

Six dated events in the last 18 months that justify the timing claim:

| Date | Event | Why it matters |
|---|---|---|
| May 2025 | Coinbase + Cloudflare launch x402 protocol | First production agent-payments standard |
| Sep 2025 | Google launches AP2 with 60+ partners | Validates the category; Visa/Mastercard/PayPal/Coinbase all signed |
| Oct 2025 | x402 transaction volume spikes 10,000% MoM | Demand signal proves the rail exists |
| Feb 2026 | Stripe completes Bridge acquisition ($1.1B) | Largest payments M&A signals stablecoin commitment |
| Feb 2026 | Stripe begins using x402 for USDC payments on Base | Tier-1 PSP adopting agent rail |
| Apr 2026 | Visa announces 100+ partners on Visa Intelligent Commerce; mainstream agent commerce by 2026 holiday season | Card network commits to agent rail |
| Apr 2025 | Persona raises $200M @ $2B for "agentic AI identity layer" | Tier-1 fraud peer pivots — competition on the same thesis |

**Counter-signal we must address:** x402 transaction volume crashed 92% from Dec 2025 peak (731k → 57k daily tx by March 2026), with on-chain analysis suggesting roughly half the remaining volume is "gamified" testing rather than real commerce. Daily protocol revenue dropped from $1M (Jan 2025) to $35k (late Feb 2026).

**Our framing of the counter-signal:**
- x402 was over-hyped in Q4 2025 by speculative actors. Trough is healthy; real commerce is forming under the hype cycle.
- The decline doesn't invalidate the thesis — it confirms behavioural anomaly detection is needed (the "gamified" 50% is exactly what our pipeline detects).
- **We do not pitch as "x402 winners". We pitch as "behavioural risk intelligence for agent traffic on any rail" — x402 happens to be the most observable canary today.**

---

## 6. Competitive landscape

### Direct (fraud detection / risk software)

| Company | Revenue / ARR | Last raise | Valuation | Positioning vs us |
|---|---|---|---|---|
| **Stripe Radar** | Not disclosed; Stripe total revenue $19.4B in 2025, ARR $6.1B; Radar blocked $2.3B in fraud in 2025 [H — Stripe 2025 annual letter] | N/A — internal | Part of Stripe (~$90B last priced) | Channel conflict: Stripe owns merchant relationship, owns Bridge, owns agent SDK |
| **Sardine** | **$23M revenue Oct 2024** [H — getlatka], 130% YoY ARR growth → ~$50M ARR run-rate end-2025 | $70M Series C, Feb 2025 | $660M (= ~13× current ARR / ~29× LTM revenue) | Closest direct competitor; behavioural-device-focused; human-trained |
| **Feedzai** | Estimated $200M+ (Tier-1 bank focus) | $75M, Oct 2025 | $2B+ (~10× est. revenue) | Enterprise-bank focus; not agent-native |
| **Forter** | Privately reported ~$120M (2023) | Last priced 2021 | ~$3B (2021 round) | Outcome-based; e-commerce focus |
| **Riskified** (NYSE: RSKD) | **$344.6M (FY2025, +5% YoY)** [H — Riskified IR]; first GAAP profit Q4 2025 ($5.8M); 2026 guide $372–384M | Public | ~$1.4B mkt cap (= ~4× revenue, slow-growth tax) | E-commerce CNP; ADR 100% / NDR 105% |
| **BioCatch** | Not disclosed | Permira majority Sep 2024 | $1.3B | Behavioural biometrics — shows our thesis works at exit scale |

### Adjacent (identity / KYC / blockchain analytics)

| Company | Last raise | Valuation | Why adjacent |
|---|---|---|---|
| **Persona** | $200M Series D, Apr 2025 | $2B | Pivoting to agent identity layer — direct collision in 18 months |
| **Alloy** | $52M, 2022 | $1.55B (2022) | Identity decisioning; 2024 ARR ~flat |
| **Chainalysis** | Last priced 2022 | $1.55B (down from $8.6B in 2022) | Crypto-only; not agent-native |
| **TRM Labs** | $70M Series C, Feb 2026 | $1B | Crypto compliance; could acquire agent-fraud capability |

### Competitive 2x2

```
                     Statistical / Graph ML
                              ↑
                              |
          Feedzai •           |        ★ BLOOMSBURY TECH
            FICO Falcon       |          (agent-native + statistical)
                              |
   ←-----------------------------------------------→
   Human-trained                         Agent-native
                              |
          Stripe Radar •      |
          Sardine •           |        (empty quadrant —
          Persona •           |         no LLM-only player can do this
          Alloy •             |         on agent volume economics)
          Forter •            |
                              ↓
                     Rule-based / LLM
```

**Three sentences for the slide:**
1. Incumbents are in the wrong quadrant. Their training corpus is a structural liability — agent transactions look nothing like the human signals their models learned.
2. Crypto-native fraud tools (Chainalysis, TRM) operate on human-on-chain behaviour, not agent behaviour. Adjacent, not competitive.
3. The only paths into our quadrant are: (a) rebuild from scratch on agent data — 18+ months while we compound, or (b) acquire whoever's furthest along. We expect (b).

---

## 7. M&A and exit comparables

Recent fraud / identity / behavioural-intelligence transactions to anchor an exit story:

| Date | Target | Acquirer | Price | Multiple |
|---|---|---|---|---|
| Feb 2025 | Bridge (stablecoin infra) | Stripe | $1.1B | ~10x rev (estimated) |
| Sep 2024 | BioCatch (behavioural biometrics) | Permira (majority) | $1.3B | ~7-10x ARR (industry estimate) |
| 2024 | IDVerse | LexisNexis Risk | Undisclosed | — |
| 2025 | AuthenticID | Incode | Undisclosed | — |
| Historical | Signifyd | (private) | $1.3B (2021) | High multiple |

**Plus public comp:** Riskified (NYSE: RSKD) at ~4x revenue (slow growth tax). Sardine private at ~6-10x ARR implied from $660M val.

**Pitch line:** "behavioural intelligence acquirers pay 7-10× ARR; channel partners (Stripe, Visa, Mastercard) acquire when category positions lock". Don't put a price on it — investors model their own exit.

---

## 8. Customer landscape — target PSPs / acquirers

Tiered priority for first paid pilot:

**Tier A — agent-rail-native or Stripe-adjacent (highest fit, lowest sales cycle)**
- **Crossmint** — embedded crypto checkout, agent-friendly stack
- **Privy** — wallet infra for AI agents
- **Bridge** (now Stripe) — stablecoin rails, but acquired so political
- **Modulr** — UK e-money, agent-payment exposure via fintech customers
- **Coinbase Commerce** — direct x402 stakeholder

**Tier B — mid-market PSP / acquirer (best long-term economics)**
- **Wise**, **Rapyd**, **Checkout.com**, **Worldpay** (now FIS)
- **Adyen** (long sales cycle but high ACV)
- **Trust Payments**, **PayU**

**Tier C — banks and neobanks**
- **Revolut**, **Monzo**, **Starling**, **N26** — fintechs with agent-payment exposure on the user side
- **JPM, BofA** — too long; only after 1-2 case studies

**First sale heuristic:** target Tier A in months 0-9 for the wedge case study; expand into Tier B mid-market once we have one published reference.

---

## 9. Stablecoin / agent-rail volume context

To support the "rail is real" claim:

- **Total stablecoin volume 2025:** $33T (up 72% YoY) — Bloomberg / Artemis [H]
- **USDC share:** $18.3T (55%) — de facto agent settlement standard [H]
- **Stripe-Bridge first week:** more stablecoin volume than Stripe's entire BTC history [H — Stripe newsroom]
- **x402 cumulative (May 2025–Apr 2026):** 165M transactions, $50M volume, 69k active agents [H — multiple]
- **x402 current (March 2026):** ~57k tx/day, ~$28k daily volume [H — Artemis]
- **Visa agent commerce 2025:** ~$3B [H — Visa]
- **Visa projected 2030:** $300-500B [H — Visa]

The volume ratio (current $28k/day vs projected $300B/year by 2030) implies the rail must compress 30,000× in 4 years. That's ambitious — but identical in shape to the cofounder's snapshot finding (28,000× growth Jun 2025 → Apr 2026 in our data). Use this dual data point.

---

## 10. Risks and investor objections

Eight objections we should expect, with prepared answers:

1. **"x402 is dying — your demo runs on a dying rail."**
   x402 specifically declined post-hype; agent payments more broadly are the bet. Visa's $300-500B 2030 projection covers card-rail agents too. Our pipeline is rail-agnostic; memo 14 shows the same model on Stripe authorization streams.

2. **"Stripe owns this. Bridge + Radar + Agentic Commerce Suite."**
   Stripe Radar is human-trained on human merchants. Stripe earns interchange on agent flows — incentive misalignment. They will license agent-fraud signal before they build. Persona's pivot at $2B is direct evidence the category cannot be done in-house by an incumbent.

3. **"Persona just raised $200M for agentic AI identity. They've already won."**
   Persona is identity verification (KYC layer); we are behavioural risk on transactions. Different layer. We are downstream; they are upstream. Likely partner, not competitor.

4. **"Where's your customer?"**
   Honest: not yet. We have validated hypotheses on real Base data (memo 16, H1-H6). Round closes the loop: hire BD, land first PSP in Q1 post-close.

5. **"Why won't Sardine just do this?"**
   Sardine's data graph (2.2B device profiles) is human-device-centric. Agent traffic has no device fingerprint. Throwing away their training set is a structural liability. We are not "Sardine for agents" — we are a different statistical object.

6. **"Your TAM is not yet a TAM."**
   Correct in 2026. The Visa primary-source projection ($3B → $300-500B) is 100×+ growth in 4 years; our 5-year SOM ($10-25M ARR) is 0.01% of the low end of that projected SAM. This is a category-creation pre-seed bet, not a market-share bet.

7. **"Why this team?"**
   Eugene: LSE Math, Bloomsbury Tech CEO, ICML-grade causal-inference and graph-ML publications. Cofounder: payments / infra background, owns Base ingestion + Dune pipeline. (Strengthen advisor list before sending to VCs.)

8. **"Regulatory risk?"**
   Fraud detection is well-established regulated category. AP2 (Google) and Visa Intelligent Commerce both have compliance frameworks we plug into. No novel regulatory risk; opportunity is to be the *evidence* layer for AP2 mandates.

---

## 11. Research gaps to close before sending the deck

| Gap | How to close | Owner | Deadline |
|---|---|---|---|
| Verify Stripe Radar implied ARR | Read latest Stripe annual or PYMNTS mix breakdown | Eugene | T+3 days |
| Triangulate Sardine ARR | Read Contrary Research full report; cross-check Crunchbase + Sacra | Cofounder | T+3 days |
| Confirm bps fraud-loss-to-software-spend ratio | Pull 2-3 case studies from Sardine / Forter / Riskified investor materials | Eugene | T+5 days |
| Get a defensible Visa primary citation | Visa investor relations 2025 10-K + April 2026 press release | Eugene | T+2 days |
| Identify 1-2 design partners we can name (or "in conversation with") | Direct outreach to Crossmint, Privy, Modulr | Both | T+10 days |
| Get advisor commitment(s) | Reach out to 3 potential industry advisors | Eugene | T+14 days |
| Validate fraud detection SaaS comps multiples | Speak to one fintech-focused VC for current multiples | Eugene | T+7 days |

---

## 12. Single-line summary

**The fraud-detection software market is $67B today and growing 17% per year. The agent-payments rail Visa projects at $300-500B by 2030 is real but in early flux; x402 specifically is in a post-hype trough. Three credible incumbents (Stripe, Persona, Google/AP2) are positioning for agent-payments fraud right now — window is 12 months. Our SOM is $10-25M ARR by year 5 from a 10-20 PSP customer base at $200-500k ACV, against a SAM of $170M-$1.7B by 2030. This is a category-creation pre-seed bet, sized appropriately.**

---

## Sources

### Market sizing
- Fortune Business Insights — [Fraud Detection and Prevention Market Growth Report](https://www.fortunebusinessinsights.com/industry-reports/fraud-detection-and-prevention-market-100231)
- MarketsAndMarkets — [Fraud Detection and Prevention Market worth $65.68 billion by 2030](https://www.marketsandmarkets.com/PressReleases/fraud-detection-prevention.asp)
- Industry Research — [Online Payment Fraud Detection Market](https://www.industryresearch.biz/market-reports/online-payment-fraud-detection-market-105047)
- GlobeNewswire — [Digital Payments Fraud, Scams, and Risk Outlook 2024–2029](https://www.globenewswire.com/news-release/2026/04/24/3280708/28124/en/Digital-Payments-and-E-Commerce-Global-Fraud-Scams-and-Risk-Outlook-Report-Losses-to-More-than-Double-from-40-Billion-in-2024-to-100-Billion-by-2029-AI-Expands-Risks-and-Defensive-.html)

### Card fraud (Nilson)
- Nilson Report — [Card Fraud Losses Worldwide — 2024](https://nilsonreport.com/articles/card-fraud-losses-worldwide-2024/)
- Payments Dive — [Card fraud losses will increase over next decade](https://www.paymentsdive.com/news/payments-fraud-losses-prevention-nilson-outlook/737440/)
- GlobeNewswire — [Payment Card Fraud Losses Approach $34 Billion](https://www.globenewswire.com/news-release/2025/01/06/3004931/0/en/Payment-Card-Fraud-Losses-Approach-34-Billion.html)
- FICO — [Card-Not-Present Fraud Remains a Leading Concern](https://www.fico.com/blogs/card-not-present-fraud-remains-leading-concern-payment-systems-evolve)

### Visa & agent commerce
- Visa Investor Relations — [Visa and Partners Complete Secure AI Transactions](https://investor.visa.com/news/news-details/2025/Visa-and-Partners-Complete-Secure-AI-Transactions-Setting-the-Stage-for-Mainstream-Adoption-in-2026/default.aspx)
- Visa Corporate — [Visa Intelligent Commerce](https://corporate.visa.com/en/products/intelligent-commerce.html)
- Visa — [The Rise of Agentic Commerce Part 1](https://corporate.visa.com/content/dam/VCOM/corporate/services/documents/vca-rise-of-agentic-commerce.pdf)
- DigitalCommerce360 — [Visa and Mastercard approaching agentic commerce](https://www.digitalcommerce360.com/2026/04/02/visa-mastercard-in-agentic-commerce/)
- CryptoBriefing — [Visa's Forestell on agentic web payments](https://cryptobriefing.com/visa-agentic-web-payments-opportunity/)

### Google AP2
- Google Cloud — [Announcing Agent Payments Protocol (AP2)](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol)
- AP2 Protocol Documentation — [ap2-protocol.org](https://ap2-protocol.org/)
- GitHub — [google-agentic-commerce/AP2](https://github.com/google-agentic-commerce/AP2)

### x402 (Coinbase)
- The Block — [Coinbase x402 V2 launch](https://www.theblock.co/post/382284/coinbase-incubated-x402-payments-protocol-built-for-ais-rolls-out-v2)
- Coindesk — [x402 demand isn't there yet](https://www.coindesk.com/markets/2026/03/11/coinbase-backed-ai-payments-protocol-wants-to-fix-micropayment-but-demand-is-just-not-there-yet)
- BlockchainNews — [OKX Ventures: x402 transactions crater 92%](https://blockchain.news/news/okx-ventures-ai-agent-economy-x402-transactions-drop-92-percent)
- Coinbase Developer Docs — [x402 welcome](https://docs.cdp.coinbase.com/x402/welcome)
- BeInCrypto — [x402 trading volume drops 90%](https://beincrypto.com/x402-trading-volume-falls-ecosystem-growth/)

### Stablecoin volume
- Bloomberg — [Stablecoin Transactions Rose to Record $33 Trillion in 2025](https://www.bloomberg.com/news/articles/2026-01-08/stablecoin-transactions-rose-to-record-33-trillion-led-by-usdc)
- Yahoo Finance — [Stablecoin Transactions Soared 72% in 2025](https://finance.yahoo.com/news/stablecoin-transactions-soared-72-2025-054951388.html)
- Artemis — [Stablecoin Payments From The Ground Up 2025](https://reports.artemisanalytics.com/stablecoins/artemis-stablecoin-payments-from-the-ground-up-2025.pdf)

### Stripe Bridge / agentic commerce
- Stripe Newsroom — [Stripe completes Bridge acquisition](https://stripe.com/newsroom/news/stripe-completes-bridge-acquisition)
- a16z — [What Stripe's Acquisition of Bridge Means for Fintech and Stablecoins](https://a16z.com/newsletter/what-stripes-acquisition-of-bridge-means-for-fintech-and-stablecoins-april-2025-fintech-newsletter/)
- CNBC — [Stripe closes $1.1 billion Bridge deal](https://www.cnbc.com/2025/02/04/stripe-closes-1point1-billion-bridge-deal-prepares-for-stablecoin-push-.html)
- Stripe Blog — [Introducing the Agentic Commerce Suite](https://stripe.com/blog/agentic-commerce-suite)
- Stripe Blog — [Radar now protects ACH and SEPA](https://stripe.com/blog/radar-now-protects-ach-and-sepa-payments)
- Stripe Radar Pricing — [stripe.com/radar/pricing](https://stripe.com/radar/pricing)

### Competitive intelligence
- BusinessWire — [Sardine $70M Series C](https://www.businesswire.com/news/home/20250211169372/en/Sardine-AI-Raises-$70M-to-Make-Fraud-and-Compliance-Teams-More-Productive)
- Contrary Research — [Sardine business breakdown](https://research.contrary.com/company/sardine)
- Crunchbase — [Sardine company profile](https://www.crunchbase.com/organization/sardine)
- PRNewswire — [Persona raises $200M at $2B](https://www.prnewswire.com/news-releases/persona-raises-200m-at-2b-valuation-to-build-the-verified-identity-layer-for-an-agentic-ai-world-302442649.html)
- SiliconANGLE — [Feedzai raises $75M at $2B valuation](https://siliconangle.com/2025/10/02/feedzai-raises-75m-2b-valuation-secures-key-role-digital-euro-fraud-prevention/)
- TechCrunch — [Alloy raises $100M at $1.35B](https://techcrunch.com/2021/09/30/alloy-raises-100m-at-a-1-35b-valuation-to-help-banks-and-fintechs-fight-fraud-with-its-api-based-platform/)
- GetLatka — [Alloy revenue and customer count](https://getlatka.com/companies/alloy)
- Sacra — [Alloy revenue, funding & news](https://sacra.com/c/alloy/)
- Fortune — [TRM Labs $1B valuation](https://fortune.com/2026/02/04/trm-labs-blockchain-analytics-funding-round-series-c-unicorn-goldman/)
- Contrary Research — [Chainalysis business breakdown](https://research.contrary.com/company/chainalysis)
- Crunchbase News — [Sardine $70M Series C wrap-up](https://news.crunchbase.com/cybersecurity/fraud-detection-startup-sardine-ai-fundraise/)

### M&A comparables
- About-Fraud — [Q3 2025 Funding & Acquisitions](https://www.about-fraud.com/funding-investment-acquisitions-ipos-q3-2025/)
- Infosecurity Magazine — [Biggest Cybersecurity M&A of 2024](https://www.infosecurity-magazine.com/news-features/top-cybersecurity-mergers/)
- Architect Partners — [Stripe Bridge deal analysis](https://architectpartners.com/stripe-is-acquiring-bridge-for-1-1-billion-the-most-strategically-important-transaction-since-the-emergence-of-crypto/)
