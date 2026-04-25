# Memo Index

Append-only build log. Every memo is shipped as **`.md` (source)**, **`.tex` (typeset source)**, and **`.pdf` (built artefact)** so reviewers and the cofounder can read the rendered version directly. Memos with experimental content cite hypothesis numbers (H1--H6) validated in `experiments/` and tabulated in `results/tables/hypothesis_results.csv`.

Build command: `bash memos/build.sh` (builds all PDFs) or `bash memos/build.sh <basename>` (one).

## Strategy

- [00_pitch_script.md](00_pitch_script.md) / [.tex](00_pitch_script.tex) / [.pdf](00_pitch_script.pdf) — 2-minute pitch beat-by-beat with stopwatch timing, Q&A answers, post-pitch follow-up.
- [01_pitch_framing.md](01_pitch_framing.md) / [.tex](01_pitch_framing.tex) / [.pdf](01_pitch_framing.pdf) — Two-minute pitch, the four-beat structure, Blomfield rubric.
- [02_moat_thesis.md](02_moat_thesis.md) / [.tex](02_moat_thesis.tex) / [.pdf](02_moat_thesis.pdf) — Why behavioural risk intelligence is the defensible wedge.
- [03_open_gaps.md](03_open_gaps.md) / [.tex](03_open_gaps.tex) / [.pdf](03_open_gaps.pdf) — Compact list of unsolved problems in agentic payments.

## Assets & data

- [04_polymarket_assets.md](04_polymarket_assets.md) / [.tex](04_polymarket_assets.tex) / [.pdf](04_polymarket_assets.pdf) — Reusable code from polymarket repo, file-by-file.
- [05_data_plan.md](05_data_plan.md) / [.tex](05_data_plan.tex) / [.pdf](05_data_plan.pdf) — x402 / Base data sourcing plan, fallbacks, schema.
- [10_alternative_datasets.md](10_alternative_datasets.md) / [.tex](10_alternative_datasets.tex) / [.pdf](10_alternative_datasets.pdf) — Backup datasets and weak-label sources.
- [12_public_data_collection.md](12_public_data_collection.md) / [.tex](12_public_data_collection.tex) / [.pdf](12_public_data_collection.pdf) — No-key live x402 collection (x402.watch + Blockscout).
- [15_data_integration_plan.md](15_data_integration_plan.md) / [.tex](15_data_integration_plan.tex) / [.pdf](15_data_integration_plan.pdf) — Dune snapshots integration architecture (parallel to memo 12 live track).
- [18_dune_cto_data.md](18_dune_cto_data.md) — CTO Dune zip import, parity check with `data/raw/x402_*.parquet`, and cooked Dune-x402-baseline dataset wired into the dashboard.

## Empirically validated (with hypothesis tests)

- [07_synthetic_design.md](07_synthetic_design.md) / [.tex](07_synthetic_design.tex) / [.pdf](07_synthetic_design.pdf) — Synthetic generator design **+ H5** (silhouette 0.35, RF 5-fold acc 99.6%, macro-F1 0.997).
- [08_features_spec.md](08_features_spec.md) / [.tex](08_features_spec.tex) / [.pdf](08_features_spec.pdf) — 36-feature behavioural fingerprint **+ H6** (35/36 features at MI ≥ 0.05).
- [13_methodology_memo.tex](13_methodology_memo.tex) / [.pdf](13_methodology_memo.pdf) — Fraud detection literature, incumbent methods, and exact methodology.
- [16_snapshot_findings.md](16_snapshot_findings.md) / [.tex](16_snapshot_findings.tex) / [.pdf](16_snapshot_findings.pdf) — Pitch numbers locked **+ H1, H2, H4** (100× compression with 95% bootstrap CI [10, 1000]; Mann-Whitney p=1.4e-44; population +41% Jun→Apr after Oct exclusion).
- [17_real_data_quality.md](17_real_data_quality.md) / [.tex](17_real_data_quality.tex) / [.pdf](17_real_data_quality.pdf) — Quality caveats **+ H3** (Oct top-1 share 99.98%; gap-to-top-2 0.9997 vs 0.62 mean).

## Build

- [06_today_plan.md](06_today_plan.md) / [.tex](06_today_plan.tex) / [.pdf](06_today_plan.pdf) — Friday build log (executed).
- [11_dashboard_demo.md](11_dashboard_demo.md) / [.tex](11_dashboard_demo.tex) / [.pdf](11_dashboard_demo.pdf) — Demo dashboard narrative and screen plan.
- [14_traditional_payments_generalisation.md](14_traditional_payments_generalisation.md) / [.tex](14_traditional_payments_generalisation.tex) / [.pdf](14_traditional_payments_generalisation.pdf) — How the x402 risk engine generalises to Stripe, Visa, PSPs, banks.

## Logistics

- [09_hackathon_logistics.md](09_hackathon_logistics.md) / [.tex](09_hackathon_logistics.tex) / [.pdf](09_hackathon_logistics.pdf) — Times, venue, judging signal.
- [19_pitch_plan.md](19_pitch_plan.md) — Saturday execution plan: rehearsal cadence, lead-dataset decision, T-30/T-5 checklists, in-pitch contingencies, post-pitch follow-up.
- [20_vc_deck_plan.md](20_vc_deck_plan.md) — VC pitch deck construction plan: 14-slide structure with TAM/SAM/SOM derivation, business model, GTM, competition map, and ask. Saturday leave-behind + full deck the following week.
- [21_market_research.md](21_market_research.md) — Sourced market research: TAM ($67B → $244B), SAM ($170M-$1.7B agent fraud by 2030), competitive landscape (Sardine $660M, Persona $2B, Feedzai $2B, Stripe-Bridge $1.1B), x402 decline context, target customer list, M&A comps. Replaces placeholder figures in memo 20.

## Repositioning

- [22_runtime_repositioning.md](22_runtime_repositioning.md) / [.tex](22_runtime_repositioning.tex) / [.pdf](22_runtime_repositioning.pdf) — From "fraud detection" to "runtime risk control for autonomous payments". Six-dimension risk vector (agent-likeness · drift · coordination · policy violation · counterparty · prompt-injection), three-decision model (Allow / Review / Block), four scenario presets (incl. prompt-injected invoice), 90-day product roadmap, wedge vs Stripe Radar / Visa / Sardine / Chainalysis. Supersedes positioning in memos 01 and 02.

## Venture development

- [23_venture_plan.md](23_venture_plan.md) — Full cofounder venture-development plan: 6-layer product architecture, 90-day roadmap, ICPs, GTM strategy, pricing tiers, competitive map, defensibility thesis. Core positioning: "We make autonomous financial agents governable."
- [24_hackathon_priorities.md](24_hackathon_priorities.md) — Saturday execution plan ranked by pitch gain: Tier S (prompt-injection scenario, risk vector, rebrand), Tier A (adversarial evader, Louvain rings), Tier B (week-1 only).
- [25_improvement_ideas.md](25_improvement_ideas.md) — Ranked post-pitch gaps: real fraud labels, Louvain ring naming, adversarial evader stress test, counterfactual explanations, wider snapshot windows.

## Experimental code

| Hypothesis | Memo | Code | Verdict |
|---|---|---|---|
| H1: median tx compression ≥ 10× Jun → Apr | 16 | `experiments/snapshot_validation.py` | supported (CI [10×, 1000×], MWU p=1.4e-44) |
| H2: payer population strictly increases (excl. Oct) | 16 | same | supported under exclusion |
| H3: Oct 2025 bipartite-degenerate | 17 | same | supported (top-1=99.98%, gap-to-top-2 z=1.82) |
| H4: mean tx misleading vs median | 16 | same | supported (skew 3.6–19.7, top-5% capture 50–99.7% of volume) |
| H5: synthetic policies separate in 36-feature space | 07 | `experiments/synthetic_separation.py` | supported (silhouette 0.35; RF acc 99.6%) |
| H6: ≥ 60% of features carry MI ≥ 0.05 | 08 | same | supported (97% of features clear threshold) |

Run: `python -m experiments.snapshot_validation && python -m experiments.synthetic_separation`.
