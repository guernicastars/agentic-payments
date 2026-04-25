"use client";

import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

type Tier = "critical" | "high" | "medium" | "low";

type EmbedRow = {
  wallet: string;
  wallet_short: string;
  x: number;
  y: number;
  score: number;
  tier: string;
};

const TIER_COLOR: Record<Tier, string> = {
  critical: "#e5484d",
  high: "#f97316",
  medium: "#f2c94c",
  low: "#2dd4bf",
};

const TIER_ORDER: Tier[] = ["critical", "high", "medium", "low"];

function radiusFromScore(score: number): number {
  const s = Math.max(0, Math.min(100, score));
  return 4 + (s / 100) * 8;
}

type TooltipPayload = {
  payload?: EmbedRow & { r: number };
};

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const row = payload[0]?.payload;
  if (!row) return null;
  const color = TIER_COLOR[(row.tier as Tier) ?? "low"] ?? "#f5f7fa";
  return (
    <div className="bg-ink-800 border border-ink-700 rounded-md px-3 py-2 text-xs shadow-md">
      <div className="font-mono text-ink-50">{row.wallet_short}</div>
      <div className="text-ink-300">
        score <span className="text-ink-50">{row.score.toFixed(1)}</span>
      </div>
      <div className="text-ink-300">
        tier{" "}
        <span style={{ color }} className="font-semibold">
          {row.tier}
        </span>
      </div>
    </div>
  );
}

export default function BehaviourMap() {
  const [rows, setRows] = useState<EmbedRow[] | null>(null);

  useEffect(() => {
    let active = true;
    fetch("/data/embedding.json")
      .then((r) => r.json())
      .then((d: EmbedRow[]) => {
        if (active) setRows(d);
      })
      .catch(() => {
        if (active) setRows(null);
      });
    return () => {
      active = false;
    };
  }, []);

  const grouped = useMemo(() => {
    const out: Record<Tier, (EmbedRow & { r: number })[]> = {
      critical: [],
      high: [],
      medium: [],
      low: [],
    };
    if (!rows) return out;
    for (const r of rows) {
      const t = (TIER_ORDER as string[]).includes(r.tier)
        ? (r.tier as Tier)
        : "low";
      out[t].push({ ...r, r: radiusFromScore(r.score) });
    }
    return out;
  }, [rows]);

  const counts = useMemo(() => {
    return {
      critical: grouped.critical.length,
      high: grouped.high.length,
      medium: grouped.medium.length,
      low: grouped.low.length,
    };
  }, [grouped]);

  if (!rows) {
    return (
      <div className="bg-ink-800 border border-ink-700 rounded-lg p-4 md:p-6">
        <div className="text-ink-300">Loading…</div>
      </div>
    );
  }

  return (
    <div className="bg-ink-800 border border-ink-700 rounded-lg p-4 md:p-6 space-y-4">
      <div>
        <h2 className="text-ink-50 text-lg md:text-xl font-semibold">
          Behaviour map
        </h2>
        <p className="text-ink-300 text-sm mt-1">
          PCA projection over 8 risk factors. Each point is one wallet; colour =
          risk tier; size = composite score.
        </p>
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="x"
              name="PC1"
              tickFormatter={(v: number) => v.toFixed(1)}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="PC2"
              tickFormatter={(v: number) => v.toFixed(1)}
            />
            <ZAxis type="number" dataKey="r" range={[16, 144]} />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} content={<CustomTooltip />} />
            <Legend />
            {TIER_ORDER.map((tier) => (
              <Scatter
                key={tier}
                name={tier}
                data={grouped[tier]}
                fill={TIER_COLOR[tier]}
                fillOpacity={0.75}
                stroke={TIER_COLOR[tier]}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div className="text-ink-300 text-xs">
        Tier counts:{" "}
        <span className="text-risk-critical font-semibold">
          critical {counts.critical}
        </span>{" "}
        ·{" "}
        <span className="text-risk-high font-semibold">high {counts.high}</span>{" "}
        ·{" "}
        <span className="text-risk-medium font-semibold">
          medium {counts.medium}
        </span>{" "}
        ·{" "}
        <span className="text-risk-low font-semibold">low {counts.low}</span>
      </div>
    </div>
  );
}
