"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type TrendRow = {
  snapshot: string;
  date_label: string;
  tx_count: number;
  unique_payers: number;
  unique_merchants: number;
  median_tx_usd: number;
  mean_tx_usd: number;
  volume_usd: number;
};

type TrendPayload = {
  source: "live_snapshots" | "locked_numbers";
  rows: TrendRow[];
};

function formatDollar(v: number): string {
  if (!isFinite(v)) return "–";
  const a = Math.abs(v);
  if (a < 0.01) return `$${v.toFixed(4)}`;
  if (a < 1) return `$${v.toFixed(2)}`;
  if (a < 1000) return `$${v.toFixed(2)}`;
  return `$${Math.round(v / 1000)}k`;
}

function formatPercent(p: number): string {
  const sign = p > 0 ? "+" : "";
  return `${sign}${Math.round(p)}%`;
}

export default function TrendChart() {
  const [data, setData] = useState<TrendPayload | null>(null);

  useEffect(() => {
    let active = true;
    fetch("/data/trend.json")
      .then((r) => r.json())
      .then((d: TrendPayload) => {
        if (active) setData(d);
      })
      .catch(() => {
        if (active) setData(null);
      });
    return () => {
      active = false;
    };
  }, []);

  if (!data) {
    return (
      <div className="bg-ink-800 border border-ink-700 rounded-lg p-4 md:p-6">
        <div className="text-ink-300">Loading…</div>
      </div>
    );
  }

  const rows = data.rows;
  const first = rows[0];
  const last = rows[rows.length - 1];

  const medianRatio =
    first && last && last.median_tx_usd > 0
      ? first.median_tx_usd / last.median_tx_usd
      : 0;

  const payerPct =
    first && first.unique_payers > 0
      ? ((last.unique_payers - first.unique_payers) / first.unique_payers) * 100
      : 0;

  const sampleSizes = rows.map((r) => Math.round(r.tx_count)).join(" / ");

  const sourceLabel =
    data.source === "live_snapshots" ? "Dune live snapshots" : "Locked numbers";

  // Exclude Oct 2025 from the chart
  const chartRows = rows.filter((r) => r.date_label !== "Oct 2025");
  const excludedRows = rows.filter((r) => r.date_label === "Oct 2025");

  return (
    <div className="bg-ink-800 border border-ink-700 rounded-lg p-4 md:p-6 space-y-4">
      <div>
        <h2 className="text-ink-50 text-lg md:text-xl font-semibold">
          12-month trend (Jun 2025 → Apr 2026)
        </h2>
        <p className="text-ink-300 text-sm mt-1">
          Median transaction value compressed 100× while agent population grew
          41%. Oct 2025 (highlighted) excluded from the headline trend —
          bipartite-degenerate (single merchant captured 99.98% of volume).
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-ink-900 border border-ink-700 rounded-md p-3">
          <div className="text-ink-500 text-xs uppercase tracking-wide">
            Median tx Jun → Apr
          </div>
          <div className="text-ink-50 text-2xl font-semibold mt-1">
            {Math.round(medianRatio)}×
          </div>
          <div className="text-ink-300 text-xs mt-1">
            {formatDollar(first.median_tx_usd)} → {formatDollar(last.median_tx_usd)}
          </div>
        </div>
        <div className="bg-ink-900 border border-ink-700 rounded-md p-3">
          <div className="text-ink-500 text-xs uppercase tracking-wide">
            Unique payers Jun → Apr
          </div>
          <div className="text-ink-50 text-2xl font-semibold mt-1">
            {first.unique_payers} → {last.unique_payers}
          </div>
          <div className="text-ink-300 text-xs mt-1">
            ({formatPercent(payerPct)})
          </div>
        </div>
        <div className="bg-ink-900 border border-ink-700 rounded-md p-3">
          <div className="text-ink-500 text-xs uppercase tracking-wide">
            Sample sizes
          </div>
          <div className="text-ink-50 text-2xl font-semibold mt-1">
            {sampleSizes}
          </div>
        </div>
        <div className="bg-ink-900 border border-ink-700 rounded-md p-3">
          <div className="text-ink-500 text-xs uppercase tracking-wide">
            Source
          </div>
          <div className="text-ink-50 text-2xl font-semibold mt-1">
            {sourceLabel}
          </div>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartRows}
            margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date_label" />
            <YAxis
              yAxisId="left"
              scale="log"
              domain={["auto", "auto"]}
              allowDataOverflow
              tickFormatter={(v: number) => formatDollar(v)}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              scale="log"
              domain={["auto", "auto"]}
              allowDataOverflow
              tickFormatter={(v: number) => formatDollar(v)}
            />
            <Tooltip
              formatter={(v: number | string) =>
                typeof v === "number" ? formatDollar(v) : v
              }
            />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="median_tx_usd"
              name="Median tx (USD)"
              stroke="#2dd4bf"
              strokeWidth={2}
              dot={{ r: 4 }}
              connectNulls={false}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="mean_tx_usd"
              name="Mean tx (USD)"
              stroke="#b7c0ca"
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={{ r: 3 }}
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div>
        <div className="text-ink-300 text-sm font-medium mb-2">
          All snapshots
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-ink-500 text-left border-b border-ink-700">
                <th className="py-2 pr-3 font-medium">Snapshot</th>
                <th className="py-2 pr-3 font-medium">Date</th>
                <th className="py-2 pr-3 font-medium text-right">Tx count</th>
                <th className="py-2 pr-3 font-medium text-right">Payers</th>
                <th className="py-2 pr-3 font-medium text-right">Merchants</th>
                <th className="py-2 pr-3 font-medium text-right">Median</th>
                <th className="py-2 pr-3 font-medium text-right">Mean</th>
                <th className="py-2 pr-3 font-medium text-right">Volume</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => {
                const excluded = r.date_label === "Oct 2025";
                const stripe = i % 2 === 0 ? "bg-ink-900/40" : "";
                const rowClass = excluded
                  ? "bg-risk-critical/10 text-ink-50"
                  : `${stripe} text-ink-300`;
                return (
                  <tr
                    key={r.snapshot}
                    className={`${rowClass} border-b border-ink-700/60`}
                  >
                    <td className="py-2 pr-3">{r.snapshot}</td>
                    <td className="py-2 pr-3">{r.date_label}</td>
                    <td className="py-2 pr-3 text-right">
                      {Math.round(r.tx_count)}
                    </td>
                    <td className="py-2 pr-3 text-right">
                      {Math.round(r.unique_payers)}
                    </td>
                    <td className="py-2 pr-3 text-right">
                      {Math.round(r.unique_merchants)}
                    </td>
                    <td className="py-2 pr-3 text-right">
                      {formatDollar(r.median_tx_usd)}
                    </td>
                    <td className="py-2 pr-3 text-right">
                      {formatDollar(r.mean_tx_usd)}
                    </td>
                    <td className="py-2 pr-3 text-right">
                      {formatDollar(r.volume_usd)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {excludedRows.length > 0 && (
          <div className="text-ink-500 text-xs mt-2">
            Excluded snapshot ({excludedRows.map((r) => r.date_label).join(", ")})
            shown highlighted in red.
          </div>
        )}
      </div>
    </div>
  );
}
