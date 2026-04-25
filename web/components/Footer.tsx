type Memo = {
  number: string;
  filename: string;
  title: string;
  description: string;
};

type DecisionMode = {
  label: string;
  description: string;
  borderClass: string;
};

const memos: Memo[] = [
  {
    number: "00",
    filename: "00_pitch_script",
    title: "Pitch script",
    description: "2-minute beat-by-beat with stopwatch timing",
  },
  {
    number: "01",
    filename: "01_pitch_framing",
    title: "Pitch framing",
    description: "The four-beat structure, Blomfield rubric",
  },
  {
    number: "02",
    filename: "02_moat_thesis",
    title: "Moat thesis",
    description: "Why behavioural risk intelligence is the wedge",
  },
  {
    number: "03",
    filename: "03_open_gaps",
    title: "Open gaps",
    description: "Unsolved problems in agentic payments",
  },
  {
    number: "04",
    filename: "04_polymarket_assets",
    title: "Polymarket assets",
    description: "Reusable code from the prior repo",
  },
  {
    number: "05",
    filename: "05_data_plan",
    title: "Data plan",
    description: "x402 / Base data sourcing, schema, fallbacks",
  },
  {
    number: "06",
    filename: "06_today_plan",
    title: "Today plan",
    description: "Friday build log",
  },
  {
    number: "07",
    filename: "07_synthetic_design",
    title: "Synthetic design",
    description: "Generator + H5 (silhouette 0.35, RF 99.6%)",
  },
  {
    number: "08",
    filename: "08_features_spec",
    title: "Features spec",
    description: "36 features + H6 (35/36 at MI ≥ 0.05)",
  },
  {
    number: "09",
    filename: "09_hackathon_logistics",
    title: "Hackathon logistics",
    description: "Times, venue, judging signal",
  },
  {
    number: "10",
    filename: "10_alternative_datasets",
    title: "Alternative datasets",
    description: "Backup datasets and weak labels",
  },
  {
    number: "11",
    filename: "11_dashboard_demo",
    title: "Dashboard demo",
    description: "Demo narrative and screen plan",
  },
  {
    number: "12",
    filename: "12_public_data_collection",
    title: "Public data collection",
    description: "No-key live x402 (x402.watch + Blockscout)",
  },
  {
    number: "13",
    filename: "13_methodology_memo",
    title: "Methodology memo",
    description: "Fraud detection literature and exact methods",
  },
  {
    number: "14",
    filename: "14_traditional_payments_generalisation",
    title: "Traditional payments generalisation",
    description: "Stripe / Visa / PSPs / banks",
  },
  {
    number: "15",
    filename: "15_data_integration_plan",
    title: "Data integration plan",
    description: "Dune snapshots integration architecture",
  },
  {
    number: "16",
    filename: "16_snapshot_findings",
    title: "Snapshot findings",
    description: "Pitch numbers + H1, H2, H4 (100×, p=1.4e-44)",
  },
  {
    number: "17",
    filename: "17_real_data_quality",
    title: "Real data quality",
    description: "Caveats + H3 (Oct bipartite-degenerate)",
  },
  {
    number: "22",
    filename: "22_runtime_repositioning",
    title: "Runtime repositioning",
    description:
      "From 'fraud detection' to 'runtime risk control'; six-dimension risk vector; 90-day product roadmap",
  },
];

const scoredItems: string[] = [
  "Behavioural fingerprints over 36 features (memo 08)",
  "6-dimension risk vector: agent-likeness, drift, coordination, policy, counterparty, prompt-injection",
  "Population-relative scoring (top 8% percentile + sub-score floor at 75/100)",
  "Structured explanations (top 3 sub-scores per alert)",
  "Replay over real recently-decoded x402 settlements OR synthetic policy classes",
];

const notScoredItems: string[] = [
  "Confirmed-fraud labels — we surface anomalies and policy breaches, not legally-confirmed fraud",
  "Custody or settlement — we are a risk and decision-support layer, not a payments processor",
  "Supply-chain identity — agent identity / runtime fingerprinting is on the roadmap (memo 18)",
  "Live SDK pre-transaction hook — currently post-fact replay; pre-transaction API is the next milestone",
  "Real-time blockchain ingest at scale — we batch-decode through public Blockscout today",
];

const decisionModes: DecisionMode[] = [
  {
    label: "Allow",
    description: "overall risk low, no critical sub-score",
    borderClass: "border-l-2 border-risk-low pl-3",
  },
  {
    label: "Review",
    description: "alert fires, top sub-score 75-89 OR tier high",
    borderClass: "border-l-2 border-risk-high pl-3",
  },
  {
    label: "Block",
    description: "top sub-score ≥ 90 OR tier critical",
    borderClass: "border-l-2 border-risk-critical pl-3",
  },
];

const memoBaseUrl =
  "https://github.com/guernicastars/agentic-payments/blob/main/memos";

export default function Footer() {
  return (
    <footer id="memos" className="scroll-mt-24 pt-8">
      <div className="border-t border-ink-700 pt-12">
        <div className="mb-10 rounded-lg border border-ink-700 bg-ink-800 p-6">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            <div>
              <h3 className="text-lg font-semibold text-ink-50">
                What we score
              </h3>
              <ul className="mt-3 space-y-2 text-sm text-ink-300">
                {scoredItems.map((item) => (
                  <li key={item} className="flex gap-2">
                    <span className="text-teal-500">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-ink-50">
                What we explicitly don&apos;t (yet)
              </h3>
              <ul className="mt-3 space-y-2 text-sm text-ink-300">
                {notScoredItems.map((item) => (
                  <li key={item} className="flex gap-2">
                    <span className="text-teal-500">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <p className="mt-6 text-xs italic text-ink-500">
            Demo uses synthetic ground-truth labels and recently-decoded public
            Base x402 settlements. Scores reflect behavioural anomaly and
            policy-breach likelihood, not legal determinations.
          </p>
        </div>

        <div className="mb-10 rounded-lg border border-ink-700 bg-ink-800 p-6">
          <h3 className="text-lg font-semibold text-ink-50">
            Three decision modes. Buyers configure thresholds per agent.
          </h3>
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
            {decisionModes.map((m) => (
              <div key={m.label} className={m.borderClass}>
                <div className="font-bold text-ink-50">{m.label}</div>
                <div className="mt-1 text-sm text-ink-300">
                  — {m.description}
                </div>
              </div>
            ))}
          </div>
        </div>

        <h2 className="text-3xl font-bold text-ink-50 md:text-4xl">
          Methodology memos
        </h2>
        <p className="mt-3 max-w-2xl text-ink-300">
          16 reports — strategy, data, validation. Each shipped as Markdown
          source, LaTeX, and built PDF.
        </p>

        <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">
          {memos.map((m) => (
            <a
              key={m.filename}
              href={`${memoBaseUrl}/${m.filename}.pdf`}
              target="_blank"
              rel="noreferrer"
              className="block rounded-lg border border-ink-700 bg-ink-800 p-5 transition hover:border-teal-500"
            >
              <div className="font-mono text-xs uppercase tracking-wide text-teal-500">
                Memo {m.number}
              </div>
              <div className="mt-2 font-semibold text-ink-50">{m.title}</div>
              <div className="mt-1 text-sm text-ink-300">{m.description}</div>
            </a>
          ))}
        </div>

        <div className="mt-16">
          <h3 className="text-lg font-semibold text-ink-50">Deploy your own</h3>
          <p className="mt-2 text-sm text-ink-300">
            Clone the repo and ship this dashboard to Vercel in one click.
          </p>
          <div className="mt-4">
            <a
              href="https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fguernicastars%2Fagentic-payments&root-directory=web&project-name=agentic-payments&repository-name=agentic-payments"
              target="_blank"
              rel="noreferrer"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img alt="Deploy with Vercel" src="https://vercel.com/button" />
            </a>
          </div>
        </div>

        <p className="mt-16 border-t border-ink-700 pt-6 text-xs text-ink-500">
          Bloomsbury Tech · Built for the AI Agents Hackathon, London · April
          26, 2026
        </p>
      </div>
    </footer>
  );
}
