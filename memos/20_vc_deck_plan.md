# 20 — VC pitch deck construction plan

**Date:** 2026-04-25 · For post-hackathon investor conversations and the YC interview if Blomfield bites.

This is a **plan to build the deck**, not the deck itself. The 2-minute hackathon pitch (memo 00) is its own artifact — the live Streamlit demo carries it. This memo plans the *real investor deck* used in 1:1 VC meetings, the YC interview, and follow-ups.

---

## Do we need a deck?

**Three artifacts, three audiences:**

| Artifact | Audience | Format | Status |
|---|---|---|---|
| 2-min spoken pitch + live demo | Blomfield Saturday 7pm | Streamlit + voice | Locked (memo 00) |
| **One-page leave-behind PDF** | Blomfield within 4h of pitch | 1 page, PDF | **Build Saturday morning** |
| **Full investor deck** | YC interview, post-hackathon VC meetings | 12–14 slides, PDF + web | **Build week of 2026-04-27** |

The 2-min pitch is unique: live demo replaces slides. The leave-behind and the full deck are both required because investors who didn't see Saturday need to read the story cold.

---

## Honest stage diagnosis

Before drafting the deck, name what we are:

- **Stage:** pre-seed / research-led pre-pre-seed. Founder + cofounder. Zero customers, zero ARR.
- **Asset:** working demo, novel data thesis, validated hypotheses (H1–H6), causal-ML team credibility.
- **Liability:** no design partner, no signed LOI, no revenue, no full-time team beyond founder.
- **Round shape:** £500k–£1.5M pre-seed at £4–8M post. Ticket sizes from angels (£25–100k) and pre-seed funds (£250–500k).
- **Traction story:** the data is the traction. 4 Dune snapshots showing 100× compression + 28,000× volume = market-shape evidence, not customer evidence.

Decks that pretend to be Series A get rejected harder than honest pre-seed decks. Lead with the *thesis*, support with the *demo*, ask appropriately.

---

## Deck structure (14 slides)

Order matters — first 4 slides decide whether they keep reading. Last 2 slides decide whether they reply.

| # | Slide | Job | Source material |
|---|---|---|---|
| 1 | Title + one-line | Brand, name, tagline | "Bloomsbury Tech — behavioural risk intelligence for agentic payments" |
| 2 | The shift | Make the problem visceral in 30s | Memo 16 trend numbers (28,000× volume, 100× median compression, +41% population) |
| 3 | The blindness | Why incumbents can't see this | Memo 00 beat 1; show "median tx = 0.001 USD vs Visa training set $30–100" |
| 4 | What we built | Product overview, screenshot of dashboard | UMAP screenshot from `results/figures/real_umap.png` + Live Tracker shot |
| 5 | How it works | 36-feature behavioural fingerprint, composite score, causal interpretability | Memo 08 (features) + memo 13 (methodology) |
| 6 | Evidence | H1–H6 hypothesis table | `results/tables/hypothesis_results.csv` |
| 7 | TAM / SAM / SOM | Market sizing | See "Market sizing approach" below |
| 8 | Business model | How we charge | See "Business model" below |
| 9 | GTM | Wedge → expand | See "GTM" below |
| 10 | Moat | Why us, why not incumbents | Memo 02 + memo 00 beat 3 |
| 11 | Competition | Honest landscape map | See "Competition map" below |
| 12 | Team | Founders + advisors | Eugene + cofounder bios, advisor list TBD |
| 13 | Roadmap + ask | Next 18 months, what we raise, what we spend on | See "Ask" below |
| 14 | Closing | Thesis in one sentence + contact | "Behavioural risk is the missing fraud layer for the agent economy. We have 18 months of structural lead." |

**Backup slides (appendix, only shown when asked):**
- A1: Detailed methodology + statistical rigour (full memo 13 contents)
- A2: Cross-rail generalisation (memo 14)
- A3: Snapshot-by-snapshot data quality notes (memo 17)
- A4: Channel conflict analysis (why Stripe Radar can't ship this)
- A5: Unit economics and pricing sensitivity
- A6: Comparable exits and acquisition logic

---

## Market sizing approach (slide 7)

Don't fabricate numbers — derive them from defensible inputs and **show your work** on the slide. VCs trust founders who reason from evidence over founders who quote McKinsey.

**TAM — total payment fraud detection market**
- Cited industry estimates: ~$50B by 2030 globally (Mordor / Allied — note as "industry estimate" not as fact)
- Stronger anchor: Stripe's reported Radar revenue (~$1B run-rate by 2024 disclosures) × competitor multiple → ~$10B current vendor market
- **Use:** $10B current → $50B by 2030

**SAM — fraud detection for non-human / agentic transaction streams**
- Bottom-up: Visa + Stripe public statements project 20–40% of e-commerce flows are agent-mediated by 2030
- Apply to global card-not-present + stablecoin payment volume (~$10T by 2030)
- 30% × $10T × 50bps fraud cost = $15B addressable spend on agent-fraud detection by 2030
- **Use:** $15B by 2030

**SOM — what we can capture in 5 years**
- Bottom-up: 50 mid-market PSPs at $200k ACV = $10M ARR plausible by year 3 with one good wedge
- **Use:** $10–25M ARR by year 5; do not claim more

**Slide treatment:** show TAM/SAM/SOM as concentric circles with the *derivation footnote* on the same slide. Cite sources inline. Investors who care will read; those who don't appreciate the rigour signal.

---

## Business model (slide 8)

Two revenue lines; lead with the simpler one.

**Primary — risk score API**
- Pricing: per scored transaction, tiered by volume
- Anchor: Sardine charges 5–15 cents per transaction; Persona is per-verification ($1–3); we land at 2–5 cents per scored agent transaction (lower per-tx because agent volume is high-frequency)
- Revenue model: PSP integrates → all agent traffic flows through scoring → MRR scales with PSP's agent volume

**Secondary — agent reputation registry (year 2+)**
- Cross-platform agent identity scoring (per memo 03 "portable agent reputation")
- Revenue: subscription to platforms that need to verify inbound agents (marketplaces, AI SaaS vendors, payment apps)

**Unit economics narrative:**
- Gross margin: 80%+ (software, no per-tx infra cost beyond compute)
- CAC: high in year 1 (founder-led sales to first 3 PSPs); falls as case studies compound
- LTV: high — switching cost is the historical scoring data PSPs accumulate with us

---

## GTM (slide 9)

Three phases on one slide. Brevity is the point — VCs hate detailed roadmaps for pre-seed companies.

**Phase 1 (months 0–9): wedge**
- Land 1 design partner: a mid-market PSP or acquirer with agent traffic exposure
- Target list: Bridge, Stripe (as partner not customer), Wise, Modulr, Rapyd, Crossmint, Privy
- Free pilot in exchange for data + case study
- Outcome: one published case study, 2–3 LOIs from adjacent PSPs

**Phase 2 (months 9–18): repeatable sales**
- 3 paying mid-market PSPs at $200k ACV → ~$600k ARR
- Hire BD lead + ML engineer
- Productise the scoring API (currently demo-grade)

**Phase 3 (months 18–36): platform**
- Agent reputation registry launches
- Move upmarket: Visa, Stripe, Adyen as channel partners or acquirers
- Cross-rail expansion (Stripe authorization streams, Visa CNP) per memo 14

**Channel logic:** the wedge is the data layer for one PSP. The endgame is *being acquired by* the channel partner once we own the agent risk dataset they'd need years to replicate.

---

## Competition map (slide 11)

2x2 matrix is overused but works here.

- **X-axis:** human-trained ↔ agent-native
- **Y-axis:** rule-based / LLM ↔ statistical / graph ML

| | Rule / LLM | Statistical / graph ML |
|---|---|---|
| **Human-trained** | Sardine, Alloy, Persona, Stripe Radar | Feedzai, FICO Falcon |
| **Agent-native** | (empty — no LLM-only player can do this) | **Bloomsbury Tech** |

Three sentences underneath:
1. *Incumbents are in the wrong quadrant. Their training data is a structural liability, not an asset.*
2. *Crypto-native fraud tools (Chainalysis, TRM) operate on human-on-chain behaviour, not agent behaviour. Adjacent, not competitive.*
3. *The only way for an incumbent to enter our quadrant is to throw away their training set or acquire us. We expect the latter.*

---

## Ask (slide 13)

Be specific. Vague asks are an experience signal.

**Raising:** £750k pre-seed at £6M post (12.5% dilution)

**Use of funds (24 months runway):**
- 1 ML engineer (productise scoring API): £450k loaded over 18 months
- 1 BD lead (PSP relationships): £200k loaded over 12 months
- Founder salary at minimum (£60k each × 2): £240k over 24 months
- Compute, data licences, legal: £150k

**Milestones unlocked:**
- 3 paying PSP customers @ $200k ACV → $600k ARR
- Case study + reference customer → seed round at £15–25M post on traction

---

## Build sequence

Two parallel tracks: leave-behind PDF (Saturday morning) and full deck (week after).

### Track A — Saturday morning leave-behind PDF (1 page)
| Time | Task | Owner |
|---|---|---|
| 10:30 → 11:00 | Assemble 1-page PDF: title + trend.png + UMAP screenshot + 3 moat bullets + contact | Eugene |
| 11:00 → 11:15 | Cofounder review + name check | Cofounder |
| 11:15 → 11:30 | Export PDF, save to phone, save to laptop, upload to Drive with shareable link | Eugene |
| | **Output:** `results/leavebehind.pdf` ready to send within 90min of pitch | |

### Track B — Full deck (week of 2026-04-27)
| Day | Task | Owner |
|---|---|---|
| Mon | Slide 1–4 (title, shift, blindness, product) — copy from memos 00, 16, 11 | Eugene |
| Tue | Slide 5–6 (how it works, evidence) — pull from memos 08, 13, hypothesis table | Cofounder |
| Wed | Slide 7–9 (TAM/SAM/SOM, business model, GTM) — needs market research time | Eugene |
| Wed | Slide 11 (competition map) — landscape research | Cofounder |
| Thu | Slide 10, 12, 13, 14 (moat, team, ask, closing) | Eugene |
| Thu | Appendix slides A1–A6 from existing memos (mostly copy-paste) | Cofounder |
| Fri | Design pass: consistent typography, colour palette matches dashboard, every slide has a single "what" | Both |
| Fri | Dry-run reading: 10 min walk-through with stopwatch (target 12 min for full deck) | Eugene |
| Sat | External review: send to 2 trusted operators / advisors for feedback | Eugene |
| Sun | Revise based on feedback; lock v1 | Eugene |

---

## Tooling

- **Format:** Pitch.com or Google Slides for collaboration; export PDF for distribution
- **Backup:** also ship as Notion page (web view) for VCs who prefer scrolling
- **Version control:** v1.0 = locked first send; iterate to v1.1 / v1.2 with changelog. Date every PDF in the filename
- **Tracking:** use DocSend or Pitch's built-in to see which slides VCs linger on — feedback loop for revisions

---

## Distribution sequence

1. **T+0 (within 90min of pitch):** leave-behind PDF to Blomfield only
2. **T+48h:** full deck v1.0 sent to Blomfield (separately, after he has the leave-behind)
3. **T+1 week:** deck to 5 warm investor intros (don't blast cold)
4. **T+2 weeks:** small revisions based on first VC feedback → v1.1
5. **T+4 weeks:** if traction signals positive (multiple second meetings) → start formal raise

---

## Anti-goals for the deck

- Don't claim revenue or signed customers we don't have
- Don't fabricate TAM with consultancy reports — show derivation
- Don't include a hockey-stick projection — pre-seed VCs read those as a tell
- Don't include a "competitive moat" slide that just lists patents (we have none) — moat is data + team + channel conflict
- Don't include theology / manuscript / personal context — wrong audience
- Don't make the deck longer than 14 + 6 appendix slides

---

## What we need that we don't have yet

Track these as build tasks in week 1:

- [ ] Verified TAM source (replace placeholder Mordor with a defensible primary source)
- [ ] At least one design-partner conversation logged (even informal — "we showed it to PSP X and they want to talk")
- [ ] Crisp founder bios with 2–3 line credentials each
- [ ] One advisor commitment (an industry name to put on slide 12 — even informal advisor adds credibility)
- [ ] Leave-behind PDF template with house style
- [ ] Pitch.com or Slides workspace set up

---

## Single-line summary

**One-page leave-behind by Saturday noon. Full 14-slide deck the following week. Honest pre-seed shape, defensible TAM derivation, specific ask. Don't pretend to be Series A.**
