# agentic-payments / web

Static Next.js port of the Streamlit dashboard for Vercel. The hackathon
landing site: hero, live fraud tracker (replay), 12-month trend, behaviour
map (PCA scatter), wallet leaderboard, and 16 methodology memos.

No Python at runtime. The pre-computation step
`scripts/export_to_web.py` runs the full `LiveTracker` and writes
JSON snapshots to `web/public/data/`; the React components fetch those at
runtime and play back the stream client-side at 1 tx / second.

## Local

```bash
cd web
npm install
npm run dev
# http://localhost:3000
```

To regenerate the JSON data (only needed when the underlying
`data/processed/real_x402_payments.parquet` or scoring code changes):

```bash
# From repo root
python scripts/export_to_web.py
```

## Deploy to Vercel

The repo includes a one-click deploy button on the landing page. Manually:

```bash
cd web
vercel deploy --prod
```

Or click:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fguernicastars%2Fagentic-payments&root-directory=web&project-name=agentic-payments&repository-name=agentic-payments)

## Architecture

| Path | What |
|---|---|
| `app/page.tsx` | Server component composing client tabs |
| `app/layout.tsx` | Sticky header + dark theme |
| `components/Hero.tsx` | Pitch hero + 4 stat cards + CTAs |
| `components/LiveTracker.tsx` | Replays `/data/events.json` at 1 tx/s, fires alerts |
| `components/TrendChart.tsx` | 12-month median compression line |
| `components/BehaviourMap.tsx` | PCA scatter over 116 live wallets |
| `components/Leaderboard.tsx` | Top-25 risk leaderboard |
| `components/Footer.tsx` | 16 memo cards + Vercel deploy button |

| Data file | Built by | Used by |
|---|---|---|
| `public/data/events.json` | `export_to_web.py` -> `LiveTracker` replay | LiveTracker |
| `public/data/trend.json` | `src.viz.trend.aggregate_from_files` | TrendChart |
| `public/data/scores.json` | post-replay `score_wallets` (top-25) | Leaderboard |
| `public/data/embedding.json` | PCA over 8 risk-factor columns | BehaviourMap |
| `public/data/meta.json` | build timestamp + headline numbers | Hero |

The Streamlit dashboard at `src/viz/dashboard.py` is unchanged and remains
the in-engine demo; this port is the public-facing static site.
