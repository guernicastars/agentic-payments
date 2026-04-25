"use client";

import { useEffect, useMemo, useState } from "react";

type Tier = "critical" | "high" | "medium" | "low";

type SubscoreKey =
  | "agent_likeness_score"
  | "drift_score"
  | "coordination_score"
  | "policy_violation_score"
  | "counterparty_risk_score"
  | "prompt_injection_score";

type Subscores = Record<SubscoreKey, number>;

type ScoreRow = {
  wallet: string;
  wallet_short: string;
  score: number;
  tier: Tier;
  subscores: Subscores;
  explanation: string;
};

type ScenarioMeta = {
  key: string;
  label: string;
  description: string;
  events: number;
  alerts: number;
  leaderboard_rows: number;
  embedding_rows: number;
};

type Meta = { scenarios: ScenarioMeta[] };

const TIER_CLASS: Record<Tier, string> = {
  critical: "bg-risk-critical/20 text-risk-critical border-risk-critical/40",
  high: "bg-risk-high/20 text-risk-high border-risk-high/40",
  medium: "bg-risk-medium/20 text-risk-medium border-risk-medium/40",
  low: "bg-risk-low/20 text-risk-low border-risk-low/40",
};

const SUBSCORE_LABEL: Record<SubscoreKey, string> = {
  agent_likeness_score: "Agent-likeness",
  drift_score: "Behavioural drift",
  coordination_score: "Peer coordination",
  policy_violation_score: "Policy violation",
  counterparty_risk_score: "Counterparty risk",
  prompt_injection_score: "Prompt-injection",
};

const SUBSCORE_KEYS: SubscoreKey[] = [
  "agent_likeness_score",
  "drift_score",
  "coordination_score",
  "policy_violation_score",
  "counterparty_risk_score",
  "prompt_injection_score",
];

function topSubscore(s: Subscores): { key: SubscoreKey; value: number } {
  let bestKey: SubscoreKey = SUBSCORE_KEYS[0];
  let bestVal = -Infinity;
  for (const k of SUBSCORE_KEYS) {
    if (s[k] > bestVal) {
      bestVal = s[k];
      bestKey = k;
    }
  }
  return { key: bestKey, value: bestVal };
}

export default function Leaderboard() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [scenario, setScenario] = useState<string>("base_x402");
  const [rows, setRows] = useState<ScoreRow[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetch("/data/meta.json")
      .then((r) => r.json())
      .then((d: Meta) => {
        if (!active) return;
        setMeta(d);
        if (d.scenarios.length > 0) {
          const has = d.scenarios.some((s) => s.key === "base_x402");
          setScenario(has ? "base_x402" : d.scenarios[0].key);
        }
      })
      .catch(() => { if (active) setMeta(null); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    setRows(null);
    setSelected(null);
    fetch(`/data/scenarios/${scenario}/scores.json`)
      .then((r) => r.json())
      .then((d: ScoreRow[]) => { if (active) setRows(d); })
      .catch(() => { if (active) setRows(null); });
    return () => { active = false; };
  }, [scenario]);

  const top = useMemo(() => (rows ?? []).slice(0, 25), [rows]);
  const selectedRow = useMemo(
    () => top.find((r) => r.wallet === selected) ?? null,
    [top, selected],
  );

  return (
    <div className="bg-ink-800 border border-ink-700 rounded-lg p-4 md:p-6 space-y-4">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
        <div>
          <h2 className="text-ink-50 text-lg md:text-xl font-semibold">Wallet leaderboard</h2>
          <p className="text-ink-300 text-sm mt-1">
            Top 25 wallets by overall action risk — driven by the highest sub-score across agent-likeness / drift / coordination / policy / counterparty / prompt-injection.
          </p>
        </div>
        <label className="text-ink-300 text-sm flex items-center gap-2">
          Scenario:
          <select
            className="bg-ink-900 border border-ink-700 rounded px-2 py-1 text-ink-50 text-sm"
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            disabled={!meta}
          >
            {(meta?.scenarios ?? []).map((s) => (
              <option key={s.key} value={s.key}>{s.label}</option>
            ))}
          </select>
        </label>
      </div>

      {!rows ? (
        <div className="text-ink-300">Loading…</div>
      ) : (
        <div className="max-h-[480px] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-ink-800">
              <tr className="text-ink-500 text-left border-b border-ink-700">
                <th className="py-2 pr-3 font-medium w-10">Rank</th>
                <th className="py-2 pr-3 font-medium">Wallet</th>
                <th className="py-2 pr-3 font-medium">Tier</th>
                <th className="py-2 pr-3 font-medium">Top sub-score</th>
                <th className="py-2 pr-3 font-medium text-right w-40">Score</th>
                <th className="py-2 pr-3 font-medium">Sub-vector</th>
              </tr>
            </thead>
            <tbody>
              {top.map((r, i) => {
                const pct = Math.max(0, Math.min(100, r.score));
                const tierClass = TIER_CLASS[r.tier] ?? TIER_CLASS.low;
                const top1 = topSubscore(r.subscores);
                const isSel = selected === r.wallet;
                return (
                  <tr
                    key={r.wallet}
                    onClick={() => setSelected((cur) => (cur === r.wallet ? null : r.wallet))}
                    title={r.explanation}
                    className={`border-b border-ink-700/60 cursor-pointer ${isSel ? "bg-ink-900/60" : "hover:bg-ink-900/40"}`}
                  >
                    <td className="py-2 pr-3 text-ink-500">{i + 1}</td>
                    <td className="py-2 pr-3 font-mono text-ink-50">{r.wallet_short}</td>
                    <td className="py-2 pr-3">
                      <span className={`inline-block border rounded-full px-2 py-0.5 text-xs font-semibold ${tierClass}`}>{r.tier}</span>
                    </td>
                    <td className="py-2 pr-3 text-ink-300">
                      {SUBSCORE_LABEL[top1.key]}{" "}
                      <span className="text-ink-50 font-mono">{Math.round(top1.value)}</span>
                    </td>
                    <td className="py-2 pr-3 text-right">
                      <div className="relative h-5 w-full bg-ink-900 rounded overflow-hidden">
                        <div className="absolute inset-y-0 left-0 bg-ink-700" style={{ width: `${pct}%` }} />
                        <div className="relative flex items-center justify-end h-full pr-2 text-ink-50 font-mono text-xs">
                          {r.score.toFixed(1)}
                        </div>
                      </div>
                    </td>
                    <td className="py-2 pr-3">
                      <div className="flex items-center gap-1">
                        {SUBSCORE_KEYS.map((k) => {
                          const v = r.subscores[k];
                          return (
                            <span
                              key={k}
                              title={`${SUBSCORE_LABEL[k]}: ${Math.round(v)}`}
                              className="rounded-full bg-teal-500"
                              style={{ width: 8, height: 8, opacity: Math.max(0.15, v / 100) }}
                            />
                          );
                        })}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {selectedRow && (
        <div className="sticky bottom-0 bg-ink-900/80 border border-ink-700 rounded-md px-3 py-2 text-sm text-ink-100">
          <span className="font-mono text-ink-50">{selectedRow.wallet_short}</span>{" "}
          — <span className="text-ink-300">{selectedRow.explanation}</span>
        </div>
      )}
    </div>
  );
}
