# 14 — Generalising from x402/Base to traditional payment rails

**Date:** 2026-04-25

## Short thesis

The core product should not be "x402 fraud detection." It should be a **rail-agnostic behavioural risk engine for automated payment traffic**.

x402/Base is our first clean demo rail because it exposes machine-readable settlement traces and agent-shaped behaviour. But the same methodology can generalise to card networks, PSPs, ecommerce platforms, and digital banks if we separate:

1. **Rail adapters** — Stripe, Shopify, card authorization streams, issuer/acquirer feeds, bank transfers, stablecoins.
2. **Canonical event/entity graph** — payment events, actors, instruments, merchants, devices, orders, disputes, refunds, chargebacks.
3. **Behavioural features** — velocity, entropy, concentration, drift, coordination, fulfillment/dispute aftermath.
4. **Risk operating layer** — score, explanation, queue, action, case management, feedback labels.

The portable asset is the feature/graph/risk layer. The rail-specific work is mostly ingestion and schema mapping.

## Why this matters commercially

If we pitch only x402, we look early but narrow. If we pitch "agentic fraud detection across payment rails," x402 becomes the wedge and the broader market is:

- PSPs and acquirers that already handle card and wallet payments but cannot distinguish human checkout from autonomous agent checkout.
- Marketplaces and ecommerce platforms that need agent-aware order risk, not only card fraud risk.
- Issuers/digital banks that need to detect cardholders authorising agents, compromised agent wallets, virtual-card misuse, and API-driven purchase scams.
- Agent platforms that need a reputation/risk layer before they are trusted with higher spend limits.

The strongest phrasing: **we classify and explain machine-shaped payment behaviour, regardless of whether the final settlement rail is Base USDC, Visa, Mastercard, Stripe, Shopify Payments, ACH, or bank transfer.**

## Incumbent surfaces to map into

### Stripe

Stripe is the easiest traditional rail to prototype against because the API already exposes useful risk and payment context.

Official docs show:

- Radar risk outcomes include `risk_level`, `risk_score`, `outcome.type`, `outcome.reason`, `network_status`, and analyst-facing `seller_message`.
- Stripe reports high/elevated/normal/not-assessed/unknown risk; high risk is blocked by default and elevated risk can enter review.
- The Charge object exposes `fraud_details`, `payment_method_details`, card checks, network decline/advice codes, 3DS metadata, refund/dispute state, and payment method fingerprints.

Source anchors:

- Stripe Radar risk evaluation: https://docs.stripe.com/radar/risk-evaluation
- Stripe Charge object: https://docs.stripe.com/api/charges/object
- Stripe Radar rules: https://docs.stripe.com/radar/rules

**Adapter strategy:** pull `Charge`, `PaymentIntent`, `Review`, `Dispute`, `Refund`, `Customer`, and Checkout Session data; normalize each successful/failed attempt into a `payment_event`; join later disputes/refunds as labels. Use `payment_method_details.card.fingerprint` as an instrument node, not a raw PAN. Use Radar output as an incumbent baseline and as an input feature, not as ground truth.

**What we add:** cross-merchant/agent behavioural features if the PSP/acquirer has enough scope; otherwise merchant-local anomaly and order-risk explanations that catch structured automation Radar may rate as normal/elevated rather than highest.

### Shopify

Shopify is the best ecommerce/order-risk bridge. Its fraud analysis surfaces indicators such as AVS, CVV, IP address details, and multiple-card attempts; recommendations are low/medium/high and trained on historical transactions across Shopify stores. Shopify also supports order risk records from third-party apps.

Source anchors:

- Shopify Fraud analysis: https://help.shopify.com/en/manual/fulfillment/managing-orders/protecting-orders/fraud-analysis
- Shopify Order Risk API: https://shopify.dev/docs/api/admin-rest/2025-07/resources/order-risk

**Adapter strategy:** ingest `Order`, `Customer`, `Transaction`, `Refund`, `Fulfillment`, and `OrderRisk` resources. The canonical event becomes an **order-payment event** rather than only a settlement event. We map Shopify recommendations to `external_risk_level`, and write our own `OrderRisk` record with `accept`, `investigate`, or `cancel`.

**What we add:** agent-aware order context: purchase velocity across products, repeated checkout scripts, high SKU/value entropy, shipping/billing drift, return/refund trails, device/IP reuse, merchant-specific behavioural baselines, and clusters of orders linked by email/domain/card/device/shipping address.

### Visa

Visa direct integration is not "easy hackathon API" work. Visa Risk Manager documentation is restricted. Public Visa material describes Visa Advanced Authorization as an AI-powered in-flight risk score using VisaNet-scale data, 500+ attributes, and account history; Visa Risk Manager turns those insights into rules, case management, whitelisting/blacklisting, and reporting.

Source anchors:

- Visa Advanced Authorization + Visa Risk Manager public infographic: https://corporate.visa.com/content/dam/VCOM/corporate/solutions/documents/visa-risk-manager-cnp-global-infographic.pdf
- Visa Risk Manager developer page notes restricted access: https://developer.visa.com/capabilities/vrm/docs

**Adapter strategy:** do not plan a direct Visa integration first. Enter through an issuer, acquirer, processor, or PSP that can provide authorization events. The canonical event should support ISO 8583-like auth fields: amount, merchant category, merchant/acquirer, issuer response, AVS/CVV/3DS/ECI signals, token/PAN fingerprint, country, terminal/channel, and later fraud/chargeback labels.

**What we add:** agent-aware behaviour above the network risk score: repeated agent purchase attempts, virtual-card orchestration, merchant-hopping, velocity bursts, card-testing patterns, and graph links across card tokens, merchants, devices, accounts, and recipients.

### Mastercard

Mastercard's public material is useful as architecture confirmation. Decision Intelligence is real-time transaction risk monitoring for issuers and can score transactions across networks. Mastercard Transaction Fraud Monitoring is aimed at acquirers, PSPs, and payment facilitators at pre-authorization; it returns risk scores and includes rules management, case management, and business insights. Public docs mention minimal integration data on the order of 30 elements and near-real-time latency.

Source anchors:

- Mastercard Decision Intelligence: https://www.mastercard.com/global/en/business/cybersecurity-fraud-prevention/risk-decisioning/decision-intelligence.html
- Mastercard Transaction Fraud Monitoring: https://www.mastercard.com/global/en/business/cybersecurity-fraud-prevention/risk-decisioning/transaction-fraud-monitoring.html

**Adapter strategy:** same as Visa: enter through issuer/acquirer/processor partners, not a public self-serve API. Treat Mastercard scores as external model signals and benchmark labels, while our engine supplies additional agent-behaviour features and explanations.

**What we add:** a model specialised for automated-agent behaviour rather than generic card fraud, plus graph evidence suitable for operations teams.

## Canonical schema

The current wallet-centric schema should become an entity-centric schema.

### `payment_event`

Minimum portable fields:

- `event_id`
- `rail` — `x402`, `stripe`, `shopify`, `visa_auth`, `mastercard_auth`, `ach`, `bank_transfer`
- `event_time`
- `amount`
- `currency`
- `status` — authorised, captured, failed, blocked, refunded, disputed
- `payer_entity_id`
- `payee_entity_id`
- `instrument_id` — wallet, card fingerprint/token, bank account fingerprint, payment method id
- `merchant_id`
- `order_id`
- `channel` — API, browser checkout, mobile, POS, hosted checkout, agent platform
- `method_family` — card, wallet, stablecoin, bank debit, bank transfer
- `external_risk_score`
- `external_risk_level`
- `external_decision`
- `raw_ref`

### `entity`

Nodes in the graph:

- payer/customer/account
- wallet
- card token/fingerprint
- bank account fingerprint
- merchant
- order
- device/browser/session
- email/phone/domain
- IP/ASN/geography
- shipping/billing address hash
- agent identity / delegated credential / API key where available

### `label_event`

Labels arrive late and with varying quality:

- chargeback
- confirmed fraud
- manual review decision
- issuer decline/approval
- Radar high/elevated/normal
- Shopify high/medium/low recommendation
- refund/return abuse
- account takeover confirmed
- customer complaint/scam report
- AML/sanctions alert

## Feature families that transfer

The current 36 x402 features map well, but we need rename them from wallet-specific to actor/entity-specific.

| Current x402 family | Traditional rail equivalent |
|---|---|
| Inter-arrival regularity | checkout/payment attempt velocity, retry cadence, subscription/payment schedule regularity |
| 24h uniformity | always-on checkout/API automation across local night hours |
| Gas tightness | request/checkout automation tightness, repeated browser/device fingerprints, API-idempotency patterns |
| Counterparty concentration | merchant/SKU/recipient concentration |
| Method concentration | payment method/card/BNPL/wallet concentration, 3DS strategy concentration |
| Burst intensity | card testing, bot checkout waves, promo/refund abuse waves |
| Late counterparty drift | account takeover or compromised agent suddenly buying from new merchants/SKUs/recipients |
| Coordination | multiple accounts/cards/devices/IPs hitting same merchant/SKU/address/payment pattern in short windows |

Additional traditional-payment features:

- AVS/CVV outcomes and mismatch patterns.
- 3DS/ECI/friction outcomes and step-up bypass/failure history.
- Device/browser/session entropy.
- Email/domain/phone age and reuse.
- Shipping/billing/geography distance and drift.
- Merchant category and SKU risk.
- Authorization decline/advice codes and retry behaviour.
- Capture delay, refund speed, partial refund patterns.
- Chargeback/dispute labels and reason codes.
- Fulfillment risk: digital vs physical, shipping speed, address forwarding, pickup point usage.

## Architecture change

Do this in three layers:

1. `src/ingest/adapters/`
   - `x402.py`
   - `stripe.py`
   - `shopify.py`
   - `card_auth.py`
   - each adapter emits `payment_event`, `entity`, `edge`, and `label_event` tables.

2. `src/features/`
   - rename wallet features conceptually to actor features.
   - aggregate by `payer_entity_id`, `instrument_id`, `merchant_id`, and `agent_id`.
   - keep rail-specific feature namespaces for AVS/CVV/3DS/gas/calldata.

3. `src/models/`
   - one composite behavioural score.
   - optional rail-specific calibration layers.
   - graph clustering over typed entity edges.
   - external risk scores as features, never as final truth.

## Product wedges by data accessibility

### Easy: Stripe merchant/acquirer pilot

Ask one Stripe merchant or marketplace for exported charges, disputes, refunds, customers, and Checkout Sessions. We can build a first traditional-rail demo from CSV/API exports.

What we can prove:

- Radar baseline vs our behavioural score.
- Cases where Radar says normal/elevated but behaviour is coordinated.
- Explanations tied to merchant operations.

### Easy-ish: Shopify app/order-risk pilot

Build a private Shopify app that reads orders/transactions/refunds and writes `OrderRisk` assessments.

What we can prove:

- "Investigate/cancel/accept" directly in merchant workflow.
- Better explanations than raw low/medium/high.
- Detection of order clusters rather than isolated orders.

### Hard but valuable: issuer/acquirer auth stream

Partner with an issuer, acquirer, PSP, or payment facilitator for auth stream + chargeback labels.

What we can prove:

- Pre-authorization latency and decisioning.
- Agent-aware risk on card rails.
- Graph/cascade detection across accounts/instruments/merchants.

### Hardest: direct Visa/Mastercard product integration

Not a hackathon path. Treat as eventual distribution/exit/partnership route.

## Messaging update

Current:

> Behavioural risk intelligence for agent traffic on x402/Base.

Better:

> Behavioural risk intelligence for automated payment traffic across rails. We start with x402 because it makes machine payments visible, then generalise the same fingerprinting and graph-risk engine to Stripe, Shopify, card authorization streams, and digital banks.

Pitch line:

> Existing fraud systems decide whether a payment looks like historic human fraud. We decide whether the payer behaves like an autonomous agent, whether that agent has drifted, and whether it is coordinating with other actors. That is useful on x402, but it is also exactly what Stripe merchants, Shopify stores, PSPs, acquirers, and issuers will need as agents start buying through traditional rails.

## Implementation next steps

1. Add a `PaymentEvent` schema doc and keep x402 as the first adapter.
2. Add stub adapters for Stripe and Shopify that read exported CSV/JSON before real API credentials.
3. Rename dashboard language from "wallets" to "actors" where possible, while retaining wallet-specific fields in the x402 tab.
4. Add a "Rails" filter: `Synthetic`, `x402/Base`, `Stripe`, `Shopify`, `Card auth`.
5. Add an "External risk" panel for Radar/Shopify/Visa/Mastercard scores when present.
6. Add "Action mapping":
   - Stripe: block/review/allowlist/flag/refund/monitor.
   - Shopify: accept/investigate/cancel/order-risk record.
   - Card auth: approve/decline/step-up/hold/manual review.
   - x402: allow/throttle/freeze/reputation downgrade.

## Bottom line

x402 is the sharpest demo, but the venture should be positioned around a rail-agnostic insight: **agents create behavioural traces that legacy fraud systems were not trained to recognise**. Traditional rails give us more labels and commercial buyers; x402 gives us a clean technical wedge and a story about where payments are going.
