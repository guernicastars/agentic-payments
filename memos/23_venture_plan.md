# 23 — Venture-development plan

**Date:** 2026-04-25 · Source: cofounder writeup. Repositions company from "fraud detection for agentic AI" to **runtime risk and control layer for autonomous payment agents**. Supersedes parts of memos 00/02/03/14/20 — read together, do not delete.

---

## Core recommendation

Do **not** position as generic "fraud detection for agentic AI." Too broad, vulnerable because no confirmed fraud labels yet.

Stronger wedge:

> **A runtime risk and control layer for autonomous payment agents.**

Commercial:

> "We monitor, score, and control financial actions taken by AI agents before money moves."

Covers fraud, misuse, compromised agents, collusion, prompt injection, policy violations, auditability — without needing to prove every flagged event is "fraud."

---

## 1. Strategic thesis

Agentic payments moving from theory to infrastructure: Stripe Machine Payments Protocol (Mar 2026), Coinbase x402 (165M+ tx, $50M+ vol, 480K+ agents), Visa/Mastercard agentic commerce frameworks.

Real problem: existing payment-risk systems built for humans/merchants/cards/devices/accounts. Agents = new actor type, different behavioural distributions, different authorization models, different failure modes.

Move from wallet anomaly analytics → agentic payment **control** infrastructure.

---

## 2. Current asset audit

| Layer | Current state | Assessment |
|---|---|---|
| Data ingestion | x402/Base ingestion + replay | Strong demo foundation |
| Feature engineering | Behavioural fingerprinting (timing, value, gas, counterparty, method, burst, coordination) | Strongest tech asset |
| Scoring | Weighted composite + explanations | Good MVP, needs calibration |
| Frontend | Live tracker, behaviour map, leaderboard, trends | Good pitch layer |
| Synthetic data | Labels for human/random/payment-bot/compromised/collusion | Useful but not enough |
| Memos | x402 → traditional rails generalisation | Very valuable |
| **Missing product** | Runtime control, policy, review queue, agent identity, labels | **Biggest gap** |

Current single suspiciousness score compresses 5 distinct things — split into:

1. Agent-likeness
2. Anomaly/drift
3. Coordination/collusion
4. Policy violation
5. Fraud likelihood

---

## 3. Product positioning

| Option | Audience | Tagline |
|---|---|---|
| A | Fintech/security buyers | Runtime risk control for autonomous payments |
| B | AI-agent companies | Payment safety layer for AI agents |
| C | Investors | Risk infrastructure layer for the agentic economy |
| D | x402/Web3 | Behavioural intelligence for machine-to-machine payments |

**Preferred one-liner:** "We help payment providers, agent platforms, and marketplaces detect, explain, and control risky financial actions by AI agents."

Sells to Stripe-likes, x402 ecosystems, agent marketplaces, PSPs, acquirers, banks, enterprises with internal purchasing agents.

---

## 4. Core wedge

Agent-behaviour risk signals that legacy fraud systems do not model well.

| Legacy signal | Agentic signal |
|---|---|
| Device fingerprint | Agent identity / runtime / model+tool fingerprint |
| User login anomaly | Delegated authority anomaly |
| Card velocity | Autonomous tx cadence |
| Merchant category risk | Agent task-context risk |
| IP/geo | Agent/tool execution environment |
| Chargeback history | Agent drift + policy breach |
| Known fraud account | Coordinated agent cluster |
| Manual user intent | Prompt/tool/payment intent mismatch |

Pitch:
> "This transaction may look legitimate to the payment processor, but the agent behaviour that produced it is abnormal."

Don't compete head-on with Radar / Visa. Be the **signal layer**.

---

## 5. Target product architecture (6 layers)

### Layer 1: Event ingestion

Event types:
```
payment_event
agent_action_event
tool_call_event
authorization_event
merchant_event
invoice_event
account_event
review_event
label_event
```

Sources: x402/Base, simulated agent runtime traces, mocked Stripe-like adapter, merchant/vendor/invoice metadata, manual review labels.

Mocked Stripe-like early = proves rail-agnostic.

### Layer 2: Canonical entity graph

Move wallet-centric → entity-centric.

Entities: Agent, User, Business, Wallet, Card, Bank account, Merchant, Vendor, Invoice, PaymentIntent, Tool, Model/runtime, Session, Device/env, Counterparty, Reviewer.

Relationships:
```
Agent acts_for User
Agent belongs_to Business
Agent used Tool
Agent read Invoice
Agent proposed PaymentIntent
PaymentIntent executed_as PaymentEvent
PaymentEvent paid Merchant
PaymentEvent funded_by Wallet/Card/Bank
Reviewer approved/rejected Case
```

### Layer 3: Behavioural fingerprinting (4 modules)

**Module A — Agent-likeness:** 24/7 uniformity, periodic timing, low IAT variance, repetitive amounts, repetitive method calls, low semantic diversity, high tool-call regularity. Classification, not accusation.

**Module B — Drift/compromise:** new counterparties, new sizes, new geos/rails/currencies, new tools, new merchant cats, new windows, new invoice sources, new approval routes. **Highest-value.**

**Module C — Coordination/collusion:** simultaneous bursts, shared counterparties, repeated motifs, ring flows, shared funding/withdrawal, shared tool/runtime infra, cross-agent timing correlation.

**Module D — Prompt/tool/payment mismatch:** missing from MVP, **crucial**.
Examples: user asks compare hotels → agent buys; user authorizes £100 → agent attempts £1000; invoice contains "ignore prior instructions"; agent reads vendor A invoice but pays vendor B; payment details change after untrusted content.

Turns "payment analytics" → "agentic runtime control."

### Layer 4: Risk scoring (vector, not scalar)

```
agent_likeness_score
drift_score
coordination_score
policy_violation_score
counterparty_risk_score
prompt_injection_risk_score
overall_action_risk
```

Enables: "Low counterparty risk but high policy violation — amount exceeds delegated limit." Or: "Highly agent-like but low risk — stable behaviour, known counterparties." Without this split: flag all successful automation as suspicious → adoption dies.

### Layer 5: Policy engine

Explicit rules:
```
max £500/tx
max £2000/day
approved vendors only
no new beneficiaries
no bank detail changes
no crypto unless pre-approved
require approval for first-time merchants
block on prompt-injection detected
escalate if invoice ≠ historical vendor record
```

Answers not just "risky?" but **"was the agent allowed?"** That's what banks/PSPs/enterprises pay for.

### Layer 6: Decision + review workflow

Every high-risk event → case.

Case page: attempted action, agent identity, user instruction, tool calls, docs read, payment details, policy triggered, anomalies, explanation, recommended action, reviewer decision, outcome, audit trail.

Decisions: Allow / Allow+monitor / Require user confirm / Step-up auth / Human review / Block / Freeze credential / Flag counterparty / Investigation.

---

## 6. Roadmap

### Phase 0 — Reposition MVP (immediate)

**Headline:** "Fraud detection for agentic AI" → "Runtime risk control for autonomous payments."

**Subheadline:** "We fingerprint agent payment behaviour, detect drift and coordination, and explain risky financial actions before money moves."

**Language use:** risky action, anomalous behaviour, compromised agent, collusive cluster, policy violation, review queue, payment firewall, agentic transaction monitoring.

**Avoid:** "fraud detected", "criminal", "confirmed fraud", "guaranteed prevention".

**Disclaimer:** "Current demo uses synthetic labels and public x402 behavioural data. It identifies anomalous and risky patterns, not legally confirmed fraud."

### Phase 1 — Commercially legible demo (1–2 weeks)

Four scenarios:

1. **Normal agent payment** — known API provider → Allow / low / known counterparty, normal amount, stable cadence
2. **Compromised agent** — sudden new wallet at unusual freq → Human review / high / new counterparty, abnormal burst, drift
3. **Collusive ring** — multi-agent same endpoint → Block/escalate / critical / synced multi-wallet, shared counterparty
4. **Prompt-injected invoice** — hidden instruction to change address → Block / critical / untrusted document altered payment instruction

Scenario 4 = proves agentic specificity.

### Phase 2 — Canonical event model (2–4 weeks)

Schemas (decouple from x402-only):

```
payment_event { id, ts, rail, amount, currency, payer_entity_id, payee_entity_id,
  agent_id, user_id, merchant_id, instrument_id, status, raw_payload }

agent_action_event { id, ts, agent_id, session_id, user_instruction, action_type,
  action_summary, tool_name, target_entity_id, confidence, raw_trace }

authorization_policy { id, agent_id, max_tx_amount, daily_limit, approved_counterparties,
  allowed_tools, can_create_payees, can_modify_payment_details, requires_review_conditions }

risk_score { id, event_id, score_type, score_value, top_factors, explanation, model_version }

case { id, event_id, status, assigned_to, recommended_action, reviewer_decision,
  notes, created_at, resolved_at }
```

Goal: prove product can ingest any rail.

### Phase 3 — Split scoring (2–3 weeks)

Single score → vector (see Layer 4). Explanations: "Critical risk driven primarily by policy violation and prompt-injection risk, not by payment amount."

### Phase 4 — Policy control (3–5 weeks)

Configurable policies + **policy simulation**: "What would have happened last month if this policy were enabled?" Reduces deployment fear. Decision modes: Monitor / Warn / Require approval / Block.

### Phase 5 — Review queue + audit (3–4 weeks)

Pages: Live alerts, Case queue, Case detail, Agent profile, Counterparty profile, Policy config, Label feedback, Audit export.

Reviewer labels: Legitimate / Suspicious / Policy violation / Fraud confirmed / False positive / Needs more info. **This creates the future training set.**

### Phase 6 — Agent-runtime integration (4–8 weeks)

```js
risk.checkAction({
  agent_id, user_id, action_type: "payment",
  amount, currency, counterparty,
  user_instruction, tool_trace, documents_read, proposed_payment
})
→ { decision: "review", overall_risk: 87,
    scores: { policy_violation: 95, drift: 71, prompt_injection: 40, coordination: 12 },
    reasons: [...], required_action: "human_approval" }
```

Pre-tx mode (more valuable) + post-tx mode.

---

## 7. Data strategy

| Stage | Source | Use |
|---|---|---|
| 1 | Synthetic + public x402 | feature/scoring logic, attack scenarios, demos, regression tests |
| 2 | Partner data | x402 provider / agent marketplace / crypto gateway / fintech sandbox / procurement-agent startup / hackathon sponsor / merchant logs. **Ask:** "anonymized agent payment/action logs → we return behavioural risk report." |
| 3 | Labels | human review, chargebacks, disputes, refunds, complaints, bans, policy violations, test attacks, confirmed prompt-injection, cluster investigations. `label_event` table from day 1. |
| 4 | Eval benchmark | **Agentic Payment Risk Benchmark v0.1** — normal recurring, high-freq legit API, compromised drift, collusive ring, prompt-injected invoice, unauthorized beneficiary, refund abuse, synthetic merchant laundering, tool-call mismatch, delegated-limit breach. Marketing asset + paper. |

---

## 8. Technical roadmap

**Month 1 — Product hardening**
Build: canonical schema, risk vector, 4 demo scenarios, improved explanations, case queue mock, policy v0, API mock.
Improve: README, demo script, landing page, architecture diagram, threat model, eval page.
Remove/soften: unsupported fraud claims, overclaimed synthetic accuracy, real-world fraud claims.

**Month 2 — Runtime control prototype**
risk.checkAction() API, sample LangChain/OpenAI Agents/MCP integration, mock payment-agent demo, prompt-injection scenario, delegated authority engine, review workflow v0.
Output: AI agent tries to pay invoice → system allows/reviews/blocks. **This is the customer-winning demo.**

**Month 3 — Partner pilot package**
Data import templates, risk report generator, entity profile, policy simulation, analyst dashboard, CSV/JSON export, SOC2 draft.
Produce: 10p pilot report template, 1p buyer brief, 12-slide investor deck, architecture note, API docs.
Pilot offer: "Send us 30–90 days of anonymized logs. We return behavioural risk map, top anomalous actors, coordination clusters, policy recommendations."

**Months 4–6 — First pilots**

| Pilot | Buyer | Value |
|---|---|---|
| A: x402 ecosystem | x402 merchant / facilitator / API marketplace / agent marketplace | Understand traffic, flag abusive clients, detect coordinated abuse, protect monetization |
| B: AI-agent platform | agent orchestration / enterprise agent / procurement agent / vertical agent startup | Policy enforcement, audit logs, trust layer, enterprise readiness |
| C: PSP/acquirer/fraud | PSP / risk vendor / fraud orchestration / bank innovation | Additive signal, early agentic coverage, risk intelligence report |

---

## 9. GTM

**Don't start with banks.** Slow. Useful for credibility, terrible for early sales.

**Start with:** agentic-commerce startups, x402/API monetization providers, AI-agent platforms, crypto payment infra, PSP innovation pilots.

**ICPs:**

| ICP | Pain | Pitch |
|---|---|---|
| x402 / machine-payment providers | unknown client behaviour, bot abuse, no risk tooling | "Classify and monitor your machine-payment traffic, detect drift/coordination, give you controls before abuse scales" |
| Agent platforms | enterprises won't trust spending agents, no audit, prompt-injection, unclear liability | "Add financial-action governance to your agents: spend limits, payment approval, risk scoring, audit trails" |
| PSPs / fraud platforms | legacy models misclassify agentic traffic, need agent features | "Agentic behavioural risk signals as API complementing your fraud stack" |
| Enterprises with internal agents | overpay, wrong vendors, malicious docs, CFO needs approval flows | "Enforce payment policies, create audit trail for every financial action by internal AI agent" |

---

## 10. Commercial packaging

| Tier | For | Price |
|---|---|---|
| 1: Monitoring | early users | £500–2,000/mo |
| 2: Control | agent platforms + enterprises | £2,000–10,000/mo or per-action |
| 3: Risk intelligence API | PSPs/fraud platforms | enterprise / pilot fee / annual |

**Pilot:** 4–6 weeks, £5k–25k. Free pilot only if logo + testimonial + data + case study + design partnership + warm intros.

---

## 11. Competitive landscape

| Incumbent | Their angle | Our angle |
|---|---|---|
| Stripe (MPP) | Process the payment | Govern the agent action **before** the payment |
| Visa / Mastercard | Secure the rails | Monitor agent behaviour across rails + runtimes |
| Coinbase x402 | Transaction layer | Risk intelligence layer |
| Sardine/Sift/Forter/Ravelin/Feedzai/Alloy | Users, merchants, devices, accounts | Agents, delegation, tool use, autonomous drift |
| Chainalysis/TRM/Elliptic | Illicit funds, wallet risk | Agentic behavioural risk + payment-intent mismatch |

---

## 12. Defensibility (5 moats)

1. **Proprietary labelled dataset** — most important moat. Sources: agent misuse, policy violations, blocked payments, confirmed FPs, prompt-injection attempts, compromised simulations, partner reviews.
2. **Agentic risk taxonomy** — own it, publish it. A1 delegated-limit breach, A2 first-time counterparty, A3 behavioural drift, A4 prompt-injected payment, A5 tool/payment mismatch, A6 multi-agent coordination, A7 synthetic merchant abuse, A8 refund/dispute exploitation, A9 credential/permission misuse, A10 human-agent collusion.
3. **Runtime integrations** — OpenAI Agents, LangChain, CrewAI, AutoGen, MCP servers, browser-use agents, payment APIs, x402 clients. Embedded **before** payment execution = hard to replace.
4. **Policy + compliance layer** — auditability. Liability ambiguity (Fenwick commentary) makes this matter.
5. **Cross-rail behavioural graph** — long-term moat is not x402, it's "we know what normal/abnormal autonomous payment behaviour looks like across rails."

---

## 13. Research agenda

| RQ | Question | Output |
|---|---|---|
| 1 | Do agents have statistically separable payment fingerprints from humans/bots/merchants? | Benchmark + paper/blog + dashboard + investor proof |
| 2 | Can we detect compromised agents via drift before loss? | Synthetic + partner eval, before/after viz, alert latency |
| 3 | Can prompt-injection-driven actions be detected via intent/action mismatch? | Attack suite, policy demo, runtime integration |
| 4 | Can multi-agent collusion be detected via temporal+graph motifs? | Coordination score, graph viz, cluster case studies |

---

## 14. Evaluation (4 layers)

1. **Synthetic scenario tests** — recall on compromised + collusion, FP on legit bots, detection latency, explanation accuracy
2. **Real public x402 descriptive** — actor count, score distribution, top features by cohort, manually inspected top alerts, cluster viz. **Do not call confirmed fraud.**
3. **Red-team simulations** — slow fraud, mimic human timing, rotate counterparties, split payments, use known merchants as cover, prompt injection in invoice text, malicious tool output. Metrics: evasion rate, detection rate, policy block rate.
4. **Partner pilot labels** — precision@K, analyst agreement, FP rate, time saved, loss prevented, policy improvements. **This is where the company becomes real.**

---

## 15. Fundraising narrative

> "Agentic payments are becoming real. Stripe, Coinbase, Visa, Mastercard, and banks are building the rails. But the risk layer is missing. Existing fraud systems know humans, cards, devices, and merchants; they don't understand autonomous agents, delegated authority, tool traces, prompt injection, behavioural drift. We built the first behavioural risk engine for autonomous payments, starting with x402 and expanding across rails."

Proof: Stripe MPP (Mar 2026), Coinbase x402 growth, Visa/Mastercard agentic commerce, Santander/Mastercard live AI-agent payment in regulated bank framework (Mar 2026), legal liability uncertainty.

**Deck (12 slides):** Title / Market shift / Problem / New risks / Solution / Demo / Tech / Why now / GTM / Business model / Moat / Team+ask.

---

## 16. Concrete product spec — V1

**Name:** AgentGuard Pay or Agentic Risk Firewall.

**Screens:**

1. **Overview** — actions monitored, payments checked, high-risk actions, blocked amount, agents under watch, policy violations
2. **Live action stream** — time | agent | action | amount | counterparty | risk | decision
3. **Case queue** — case | severity | reason | agent | counterparty | status | reviewer
4. **Case detail** — action summary, user instruction, agent trace, payment details, risk scores, policies triggered, behavioural history, recommended decision, reviewer action, audit log
5. **Agent profile** — normal window, usual counterparties, usual amounts, tool usage, risk trend, recent drift, policy limits
6. **Counterparty profile** — paid by N agents, known/unknown, cluster associations, first seen, risk history
7. **Policy builder** (no-code):
   ```
   IF amount > £500 AND counterparty is new THEN require review
   IF prompt injection risk > 80 THEN block
   IF coordination score > 85 THEN escalate
   IF vendor bank details changed THEN require approval
   ```
8. **Evaluation** — synthetic benchmark, red-team, real x402 descriptive, pilot labels (when available)

---

## 17. MVP improvements (immediate)

**Demo selector** at top: Normal payment / Compromised agent / Collusive ring / Prompt-injected invoice / Policy violation. Each shows: input → agent action → risk analysis → decision → explanation → audit log.

**Language replacements:**

| Current | Replace with |
|---|---|
| "Fraud detected" | "Risky autonomous payment action flagged" |
| "Malicious wallet" | "High-risk actor" |
| "Fraud probability" | "Action risk score" |

**Structured explanations:**
```
Top risk factors:
1. New counterparty: +24
2. Amount 4.7× above baseline: +19
3. Burst activity: +14
4. Agent policy violation: +30

Recommended action: Human review before execution.
```

**Methodology page:** threat model, feature families, scoring model, limitations, eval method, synthetic vs real, confirmed vs inferred.

**Engineering credibility:** architecture diagram, API docs, sample webhook, sample SDK call, tests badge, deployment instructions, sample event schema.

---

## 18. Legal / compliance / trust

Buyer questions: automated denial decisions? Appeals? Auditable explanations? Data storage? PII? PCI scope? Regulated payment service? Liability?

**Compliance posture (early):** "We do not move funds or custody money. We provide risk scoring, policy enforcement, and audit trails for customers' own payment workflows." Keeps you out of regulated activities.

**Security posture (path):** encryption at rest, tenant isolation, RBAC, audit logs, retention controls, PII minimization, SOC2 roadmap, signed webhooks, customer-managed keys (later).

---

## 19. Team

**Must-have:**
1. Backend/data engineer — schemas, ingestion, APIs, pipelines
2. ML/risk engineer — features, anomaly detection, eval
3. Frontend/product engineer — dashboard, case queue, policy builder
4. Commercial founder/domain lead — partnerships (agent platforms, PSPs, x402)

**Advisors:** payments fraud operator; PSP/acquirer risk lead; AI-agent security researcher; fintech compliance lawyer; on-chain analytics expert. **Highest value:** fraud/risk operator from Stripe / Adyen / Checkout.com / Visa / Mastercard / Sardine / Sift / Ravelin or large marketplace.

---

## 20. 90-day execution

| Window | Deliverables | Success criterion |
|---|---|---|
| Days 1–10: Narrative + demo cleanup | new landing copy, threat model, architecture diagram, scenario demo, softened claims, README, 2-min pitch | Smart fintech person understands product in <2 min |
| Days 11–30: Product V1 foundations | canonical schema, risk vector, policy v0, case queue mock, agent profile, API mock | Looks like a control layer, not just analytics |
| Days 31–60: Runtime agent demo | simulated purchasing/payment agent, invoice prompt-injection scenario, intent/payment mismatch detection, pre-payment risk API, review/approve/block | Demo system **prevents** bad agentic payment before money moves |
| Days 61–90: Pilot readiness | partner data import templates, pilot report template, batch scoring, policy simulation, basic auth/multi-tenant, outreach list of 50, 5–10 warm intros, 2–3 design partners | At least one real org agrees to share data or test API |

---

## 21. Outreach templates

**To x402/API providers:**
> Building behavioural risk layer for autonomous payment traffic, starting with x402. AI agents don't transact like humans — different timing, counterparty, method, burst, coordination patterns. Built prototype that fingerprints x402 actors, detects drift + coordination, explains risky activity. Would love to run lightweight analysis on anonymized traffic or collaborate on sandbox dataset. Output: risk map of agent/payment behaviour, top anomalous actors, recommended controls. Open to a short call?

**To agent platforms:**
> Building runtime risk-control layer for AI agents that can spend/purchase/refund/trigger payments. Checks agent's financial action **before** execution: violates delegated authority? counterparty new? action differs from user instruction? prompt-injection involved? behaviour drifted from baseline? Working MVP using x402/Base traces. Adding agent-runtime integrations + policy controls. Open to discussing how your team thinks about financial permissions + auditability for agents?

**To PSP/fraud:**
> Exploring new risk layer for agentic payments. As Stripe/Visa/Mastercard/Coinbase push agentic rails, gap emerging: existing fraud built around human/device/merchant baselines, but autonomous agents have distinct patterns + failure modes. Built prototype scoring agentic payment behaviour across drift, coordination, counterparty concentration, policy violation, prompt/tool/payment mismatch. Value your feedback on whether useful as additive signal for PSP/fraud teams.

---

## 22. Anti-patterns

- **Don't be "Chainalysis for x402"** — too narrow, crypto analytics box
- **Don't be "Stripe Radar for agents"** — Stripe/Visa/Mastercard/Adyen can build that internally
- **Don't claim confirmed fraud from public x402 data** — undermines credibility
- **Don't focus only on dashboards** — easy to copy. Runtime control + policies + labels + integrations are harder
- **Don't ignore legitimate agents** — must distinguish good automation from bad. Otherwise seen as anti-agent

---

## 23. Strongest framing

Not: "We detect fraud in AI payments."

But: **"We make autonomous financial agents governable."**

- What is the agent allowed to do?
- Did it follow user's intent?
- Did untrusted content manipulate it?
- Is this behaviour normal for this agent?
- Is it coordinating with other actors?
- Allow / review / block?
- Can the company prove afterwards why?

---

## 24. Top 5 immediate priorities

1. **Rebrand** as runtime risk control for autonomous payments
2. **Split single risk score** into agent-likeness, drift, coordination, policy, counterparty, prompt-injection
3. **Add agent-runtime demo**: user instruction + tool trace + invoice + attempted payment + block/review decision
4. **Build policy engine + case review queue**
5. **Start design-partner outreach** to x402 providers, agent platforms, PSP/fraud operators

That sequence: hackathon analytics demo → venture-shaped product.

---

## Add below
