type Stat = {
  value: string;
  label: string;
};

const stats: Stat[] = [
  {
    value: "100×",
    label: "median tx compression Jun 2025 → Apr 2026",
  },
  {
    value: "28,000×",
    label: "daily volume growth, same window",
  },
  {
    value: "99.6%",
    label: "RF 5-fold accuracy on synthetic policy classes",
  },
  {
    value: "97%",
    label: "of features carry MI ≥ 0.05 (memo 08)",
  },
];

const dimensions: string[] = [
  "Agent-likeness",
  "Behavioural drift",
  "Peer coordination",
  "Policy violation",
  "Counterparty risk",
  "Prompt-injection",
];

export default function Hero() {
  return (
    <section className="pt-6">
      <p className="text-xs font-semibold uppercase tracking-wide text-teal-500">
        Bloomsbury Tech · Hackathon Build · April 2026
      </p>
      <h1 className="mt-4 text-4xl font-bold leading-tight text-ink-50 md:text-6xl">
        Runtime risk control for autonomous payments.
      </h1>
      <p className="mt-6 max-w-3xl text-lg text-ink-300">
        Visa, Mastercard, and Stripe Radar were trained on a billion human
        transactions. AI agents settle in tenths of a cent through x402,
        delegate authority through tools, and read attacker-tampered invoices.
        We monitor, score, and govern financial actions taken by AI agents —
        before money moves.
      </p>

      <div className="mt-10 grid grid-cols-2 gap-4 md:grid-cols-4">
        {stats.map((s) => (
          <div
            key={s.label}
            className="rounded-lg border border-ink-700 bg-ink-800 p-5"
          >
            <div className="font-mono text-3xl text-teal-500">{s.value}</div>
            <div className="mt-2 text-sm text-ink-300">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
        <a
          href="#demo"
          className="rounded-md bg-teal-500 px-5 py-3 font-semibold text-ink-900 hover:opacity-90"
        >
          See it live →
        </a>
        <a
          href="#memos"
          className="rounded-md border border-ink-700 px-5 py-3 text-ink-100 hover:bg-ink-800"
        >
          Methodology + memos
        </a>
      </div>

      <p className="mt-8 text-center text-xs text-ink-500">
        The risk vector — every action gets a six-dimension score before a
        decision.
      </p>
      <div className="mt-3 flex flex-wrap justify-center gap-2">
        {dimensions.map((d) => (
          <span
            key={d}
            className="rounded-full border border-ink-700 bg-ink-800 px-3 py-1 text-xs text-ink-300"
          >
            {d}
          </span>
        ))}
      </div>
    </section>
  );
}
