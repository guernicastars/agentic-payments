# 08 — Behavioural fingerprint feature spec

**Date:** 2026-04-25

Per-wallet rows aggregated over a window (default: full input window). Target 30–50 features grouped into 6 families.

## A. Temporal (8)
1. `tx_count` — total transactions
2. `inter_arrival_mean_s` — mean seconds between consecutive tx
3. `inter_arrival_std_s` — std of inter-arrivals
4. `inter_arrival_cv` — coefficient of variation = std/mean (≈0 → cron, ~1 → Poisson)
5. `inter_arrival_entropy` — Shannon entropy of log-binned inter-arrivals (low → periodic)
6. `tod_uniformity` — KS distance between hour-of-day histogram and Uniform[0,24] (low = uniform = agent-like)
7. `tod_human_similarity` — KL divergence vs. canonical human time-of-day curve
8. `burstiness` — Goh & Barabási burstiness B = (σ−μ)/(σ+μ) of inter-arrivals

## B. Gas / optimisation (6)
9. `gas_price_mean_gwei`
10. `gas_price_std_gwei`
11. `gas_price_to_basefee_ratio_mean` — over network basefee at that block
12. `gas_price_to_basefee_ratio_std` — agents pathologically tight → small std
13. `gas_used_cv` — same-method-id coefficient of variation; agents reuse same calldata → small
14. `gas_optimisation_score` — composite: low std-to-basefee + low gas_used_cv (z-scaled)

## C. Value distribution (6)
15. `value_usd_mean`
16. `value_usd_median`
17. `value_usd_std`
18. `value_usd_log_std` — std of log-values; humans wide, agents narrow
19. `value_usd_entropy` — Shannon entropy of log-binned values
20. `large_value_share` — fraction of tx > 95th percentile of population

## D. Counterparty graph (6)
21. `unique_counterparties` — distinct `to_addr`
22. `counterparty_concentration_top1` — share of tx to single most-used counterparty
23. `counterparty_concentration_top3` — share to top 3
24. `counterparty_diversity_entropy` — Shannon entropy over counterparty distribution
25. `counterparty_repeat_rate` — fraction of (from, to) pairs that occur ≥2×
26. `new_counterparty_late_share` — fraction of tx in last 25% of window with previously-unseen counterparty (compromise signal)

## E. Method / call profile (5)
27. `unique_method_ids` — distinct 4-byte selectors
28. `method_concentration_top1` — share of dominant method
29. `native_transfer_share` — fraction of plain ETH transfers
30. `erc20_transfer_share` — fraction of `0xa9059cbb`
31. `success_rate` — fraction of `success=True`

## F. Burst / coordination (5)
32. `max_burst_count_60s` — peak transactions in any 60s window
33. `bursts_per_hour` — count of windows where ≥3 tx fired within 30s
34. `mean_inter_burst_minutes` — between burst centres
35. `coordination_proxy` — fraction of tx within 60s of *any other tracked wallet*'s tx (collusion signal)
36. `coordination_partner_count` — distinct wallets within 60s windows

## Implementation order

1. A + C + E (cheap, rely only on per-wallet stats) → 19 features
2. B (needs basefee join — fake basefee for synthetic) → 6 features
3. D (per-wallet aggregations on `to_addr`) → 6 features
4. F (population-level windowing — most expensive; do last) → 5 features

## Output

`data/processed/features.parquet`:
- Index: `from_addr`
- Columns: 36 features above + `tx_count` join helpers
- Plus a `policy` / `role` column when ground-truth labels available (from synthetic)

## Notes

- All features standardised (z-score) over the population *for the cluster/score step*. Raw values kept for the explanation generator ("inter_arrival_cv = 0.04 vs population median 0.81 → top-1% periodic").
- Population reference matters: agents and humans co-mingle in the population, so z-score is *within-policy-mixture*. That's fine — we want the anomaly detector to rank within whatever distribution Base actually has, not against an idealised human baseline.
