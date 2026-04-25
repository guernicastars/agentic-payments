"use client";

import { useEffect, useState } from "react";

type Tier = "critical" | "high" | "medium" | "low";

type ScoreRow = {
  wallet: string;
  wallet_short: string;
  score: number;
  tier: Tier;
  explanation: string;
};

const TIER_CLASS: Record<Tier, string> = {
  critical:
    "bg-risk-critical/20 text-risk-critical border-risk-critical/40",
  high: "bg-risk-high/20 text-risk-high border-risk-high/40",
  medium: "bg-risk-medium/20 text-risk-medium border-risk-medium/40",
  low: "bg-risk-low/20 text-risk-low border-risk-low/40",
};

function truncate(s: string, n: number): string {
  if (s.length <= n) return s;
  return `${s.slice(0, n - 1)}…`;
}

export default function Leaderboard() {
  const [rows, setRows] = useState<ScoreRow[] | null>(null);

  useEffect(() => {
    let active = true;
    fetch("/data/scores.json")
      .then((r) => r.json())
      .then((d: ScoreRow[]) => {
        if (active) setRows(d);
      })
      .catch(() => {
        if (active) setRows(null);
      });
    return () => {
      active = false;
    };
  }, []);

  if (!rows) {
    return (
      <div className="bg-ink-800 border border-ink-700 rounded-lg p-4 md:p-6">
        <div className="text-ink-300">Loading…</div>
      </div>
    );
  }

  const top = rows.slice(0, 25);

  return (
    <div className="bg-ink-800 border border-ink-700 rounded-lg p-4 md:p-6 space-y-4">
      <div>
        <h2 className="text-ink-50 text-lg md:text-xl font-semibold">
          Wallet leaderboard (live population)
        </h2>
        <p className="text-ink-300 text-sm mt-1">
          Top 25 wallets by composite behavioural risk after the full 360-tick
          replay.
        </p>
      </div>

      <div className="max-h-[480px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-ink-800">
            <tr className="text-ink-500 text-left border-b border-ink-700">
              <th className="py-2 pr-3 font-medium w-10">#</th>
              <th className="py-2 pr-3 font-medium">Wallet</th>
              <th className="py-2 pr-3 font-medium">Tier</th>
              <th className="py-2 pr-3 font-medium text-right w-40">Score</th>
              <th className="py-2 pr-3 font-medium">Explanation</th>
            </tr>
          </thead>
          <tbody>
            {top.map((r, i) => {
              const pct = Math.max(0, Math.min(100, r.score));
              const tierClass =
                TIER_CLASS[r.tier] ?? TIER_CLASS.low;
              return (
                <tr
                  key={r.wallet}
                  className="border-b border-ink-700/60 hover:bg-ink-900/40"
                >
                  <td className="py-2 pr-3 text-ink-500">{i + 1}</td>
                  <td className="py-2 pr-3 font-mono text-ink-50">
                    {r.wallet_short}
                  </td>
                  <td className="py-2 pr-3">
                    <span
                      className={`inline-block border rounded-full px-2 py-0.5 text-xs font-semibold ${tierClass}`}
                    >
                      {r.tier}
                    </span>
                  </td>
                  <td className="py-2 pr-3 text-right">
                    <div className="relative h-5 w-full bg-ink-900 rounded overflow-hidden">
                      <div
                        className="absolute inset-y-0 left-0 bg-ink-700"
                        style={{ width: `${pct}%` }}
                      />
                      <div className="relative flex items-center justify-end h-full pr-2 text-ink-50 font-mono text-xs">
                        {r.score.toFixed(1)}
                      </div>
                    </div>
                  </td>
                  <td
                    className="py-2 pr-3 text-ink-300"
                    title={r.explanation}
                  >
                    {truncate(r.explanation, 90)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
