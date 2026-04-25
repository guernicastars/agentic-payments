# 19 — Pitch plan (Saturday execution)

**Date:** 2026-04-25 · For 7pm pitch slot, central London.

The pitch script (memo 00) is the **what**. This memo is the **when, how, and contingency**. Read together: 00 = words, 19 = operations.

---

## What is being judged

Per memo 09: "founder potential via pitch", not best product. **Pitch is the deliverable, demo is velocity signal.** Tom Blomfield reads delivery, conviction, and how cleanly the gap is articulated. Optimise for *delivery quality on the locked script*, not for last-minute new content.

Implications:
1. Saturday afternoon is **rehearsal-dominant**, not feature-dominant.
2. Any new feature added Saturday must be testable in the demo flow within 30 min, otherwise revert.
3. The 2-min budget is a hard constraint — over-time is a worse signal than under-time.

---

## Lead-dataset decision (must be made by 14:00)

The dashboard has three datasets: `Synthetic stress test`, `Dune x402 + baseline`, `Public x402 Base`. The script (memo 00) opens on `Public x402 Base`. We need to commit to one **lead** narrative path before rehearsal block #2.

| Dataset | When to lead with it | Risk |
|---|---|---|
| Public x402 Base | Default (script-locked) | Smallest dataset; if Q&A pushes "is this real?" the answer is "yes but small" |
| Dune x402 + baseline | If we want to show baseline contrast directly | New, less rehearsed; adds a beat to memorise |
| Synthetic | Fallback only if both real datasets render badly on the demo machine | "Where's the real data?" risk |

**Default: keep memo 00 unchanged, open on Public x402 Base.** Use Dune as a Q&A asset only ("we also have CTO Dune pull with ordinary Base baseline as a contrast — see tab 2"). Do not add a 5th beat to the script.

---

## Saturday timeline

| Time | Block | Owner | Output |
|---|---|---|---|
| 10:00 → 10:30 | Repo sync, smoke test `make demo`, verify all 3 dataset toggles render | Eugene + cofounder | Confirmed-green local env, screenshots saved as fallback |
| 10:30 → 11:30 | Final memo cleanup; build all PDFs (`bash memos/build.sh`); confirm `13_methodology_memo.pdf` opens cleanly | Cofounder | All PDFs current, ready as backup tabs |
| 11:30 → 13:00 | Demo polish: zoom 110%, default tab = Triage, default dataset = Public x402 Base, screenshot every tab as backup | Eugene | Browser bookmarked to demo URL with right state |
| 13:00 → 14:00 | Lunch + decide lead dataset (see above) | — | Decision committed |
| 14:00 → 14:30 | **Rehearsal #1** — script, no demo, just timing | Eugene | First time-to-end measurement |
| 14:30 → 15:00 | **Rehearsal #2** — script + demo, full flow | Eugene | Demo timing tied to beats |
| 15:00 → 15:30 | **Rehearsal #3** — Q&A drill, cofounder asks the 5 questions in memo 00 | Both | Each answer ≤ 30s, no hedging |
| 15:30 → 16:00 | **Rehearsal #4** — record on phone, watch playback | Eugene | Identify filler words, dropped beats |
| 16:00 → 16:30 | Fix what playback exposed (1 fix max) | Eugene | Tightened delivery |
| 16:30 → 17:00 | **Rehearsal #5** — final, with stopwatch, in front of cofounder | Both | 120s ± 2s |
| 17:00 → 18:00 | Buffer / decompress / hydrate / re-do checklist | — | Ready state |
| 18:00 → 18:30 | Travel to venue if not already there | — | On-site early |
| 18:30 → 19:00 | T-30 setup (see below) | Both | Demo machine ready |
| 19:00 | Pitch slot | Eugene (delivery), Cofounder (backup speaker) | — |

---

## Pre-pitch checklists

### T-30 minutes
- [ ] Laptop on, full battery + plugged in, brightness at max
- [ ] Streamlit running: `make demo` (synthetic auto-builds; `make public` already cached; Dune already cached)
- [ ] Browser open to dashboard, zoom 110%, on `Public x402 Base` source, on **Behaviour Map** tab (matches script beat 2 opening)
- [ ] Second browser tab: `results/figures/trend.png` open (backup if Trend tab fails)
- [ ] Third tab: `memos/13_methodology_memo.pdf` (rigour Q&A backup)
- [ ] Fourth tab: `memos/14_traditional_payments_generalisation.pdf` (Stripe/Visa generalisation Q&A backup)
- [ ] Phone with stopwatch, charged, in pocket
- [ ] Notifications off (Slack, mail, Calendar, Messages, Discord)
- [ ] Wifi tested on venue network; if flaky, switch to phone hotspot now
- [ ] Glass of water nearby

### T-5 minutes (per memo 00)
- [ ] All four browser tabs visible/orderable in correct sequence
- [ ] Eugene reads memorised mic-glitch opener silently once: *"AI agents transact at a thousandth of a cent — Visa's models can't even see them."*
- [ ] Cofounder briefed: takeover beat is **beat 2 (demo evidence)**, not beat 1 or 3 — if Eugene fumbles, cofounder takes over there because the demo screen carries the words
- [ ] Final breath — long inhale, slow exhale × 3

---

## During-pitch contingencies

| Failure | Response |
|---|---|
| Mic dies in beat 1 | Use the memorised opener loud, walk one step toward Blomfield, project |
| Streamlit crashes mid-demo | Switch to second browser tab (`trend.png`); say *"the live console is loading — meanwhile, this is the 12-month trend that matters"* — keep moving |
| Browser tab loses state (defaults to synthetic) | Don't switch; say *"on synthetic stress data first — same pipeline runs the real data on the next tab"* and continue beat 2 from synthetic Behaviour Map |
| Time check at 1:30 says we're behind | Cut beat 4 to 15s: *"We start as the fraud signal layer for one PSP. We expand to agent reputation, AML, dispute evidence."* — skip the acquisition line |
| Time check at 1:30 says we're ahead | Add the buffer line from memo 00: *"And it ports — same pipeline runs on Stripe authorization streams."* |
| Blomfield interrupts with a question mid-pitch | Answer in ≤ 20s, then resume *"so back to where we were —"* and pick up the next beat |
| Eugene blanks completely | Cofounder steps in with *"the demo is the answer — let me show you"* and runs beat 2 from the screen |

---

## Q&A drill (rehearsal block #3)

Cofounder asks each in random order. Eugene answers in ≤ 30s, no hedging, no "great question". Memo 00 has the canned answers — drill until they come out without thinking:

1. "How is this different from Sardine?"
2. "What's your label source?"
3. "Stripe could just do this."
4. "Why not Polygon / Solana?"
5. "Bipartite oddity in Oct 2025?"

Add three Blomfield-flavoured probes (he asks founder-shape questions):

6. "Why you two?" → *"Eugene publishes causal-inference ML; cofounder owns the Base data ingestion. Together: 18 months of structural lead Sardine can't replicate."*
7. "What would you do with $500k?" → *"Hire one ML engineer to productise the score endpoint and one BD to land the first PSP pilot. Six-month runway to first paid integration."*
8. "Why now?" → *"x402 launched in production this year. Median tx dropped 100× and volume rose 28,000× in 12 months. The data shape is new and incumbents have no labelled corpus."*

---

## Post-pitch follow-up (per memo 00, expanded)

**Within 4 hours of pitch:**
- [ ] If Blomfield hands a card: thank-you DM + 1 attached PDF (one-page deck) within 90 minutes
- [ ] One-page deck = trend slide + UMAP screenshot + 3 moat bullets — already build-ready in `results/figures/`, just needs PDF assembly
- [ ] Repo invite to `guernicastars/agentic-payments` (read access; promote later)
- [ ] Methodology memo PDF link (`memos/13_methodology_memo.pdf`)

**Within 48 hours:**
- [ ] If no card: short LinkedIn message to Blomfield referencing one specific beat from his Q&A
- [ ] Debrief memo: what Q&A questions hit, what we couldn't answer cleanly, what to ship in week 1 to close those gaps

**Within 1 week:**
- [ ] If interview offered: practice the YC-style pitch (different format from 2-min hackathon) before the call
- [ ] Cold outreach to 3 mid-market PSPs (the wedge customer per the script) — anchor on "we have x402 fraud signal data, you have the merchant base"

---

## Anti-goals (do NOT do Saturday)

- Do not add a new dashboard tab Saturday morning
- Do not re-run the experiments / rebuild PDFs after 14:00 (LaTeX hangs are pitch-killing)
- Do not change the script after rehearsal #2 — only delivery-level fixes after that
- Do not switch the lead dataset after the 14:00 decision
- Do not present the manuscript / theology framing — wrong audience
- Do not mention bipolar / personal context unless Blomfield asks

---

## Single-line summary

**The pitch is locked. Saturday is delivery quality. Five rehearsals, one decision (lead dataset), zero new features.**
