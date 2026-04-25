"use client";

import { useEffect, useMemo, useState } from "react";

type Tier = "critical" | "high" | "medium" | "low";

type LiveEvent = {
  tick: number;
  tx: {
    from_addr: string;
    to_addr: string;
    value_usd: number;
    tx_hash: string;
    block_time_s: number;
    method_id: string;
  };
  population_size: number;
  warming_up: boolean;
  score: number | null;
  tier: Tier | null;
  alert: null | {
    tick: number;
    wallet: string;
    wallet_short: string;
    composite_score: number;
    tier: Tier;
    explanation: string;
    value_usd: number;
    tx_hash: string;
    to_addr_short: string;
  };
};

const TICKER_ROWS = 12;
const ALERT_ROWS = 4;
const WARMUP_THRESHOLD = 25;

const tierBorder: Record<Tier, string> = {
  critical: "border-risk-critical",
  high: "border-risk-high",
  medium: "border-risk-medium",
  low: "border-risk-low",
};

const tierBadge: Record<Tier, string> = {
  critical: "bg-risk-critical/20 text-risk-critical border border-risk-critical/40",
  high: "bg-risk-high/20 text-risk-high border border-risk-high/40",
  medium: "bg-risk-medium/20 text-risk-medium border border-risk-medium/40",
  low: "bg-risk-low/20 text-risk-low border border-risk-low/40",
};

function shortAddr(addr: string): string {
  if (!addr) return "";
  if (addr.length <= 12) return addr;
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

function formatUsd(value: number): string {
  if (!Number.isFinite(value)) return "$0";
  const abs = Math.abs(value);
  if (abs > 0 && abs < 0.01) return `$${value.toFixed(4)}`;
  if (abs < 1) return `$${value.toFixed(4)}`;
  if (abs < 100) return `$${value.toFixed(2)}`;
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function formatTime(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${r.toString().padStart(2, "0")}`;
}

export default function LiveTracker() {
  const [events, setEvents] = useState<LiveEvent[] | null>(null);
  const [cursor, setCursor] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch("/data/events.json")
      .then((r) => r.json())
      .then((data: LiveEvent[]) => {
        if (!cancelled) setEvents(data);
      })
      .catch(() => {
        if (!cancelled) setEvents([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!events || paused) return;
    if (cursor >= events.length) return;
    const id = setInterval(() => {
      setCursor((c) => {
        if (!events) return c;
        if (c >= events.length) return c;
        return c + 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [events, paused, cursor]);

  const seen = useMemo(() => {
    if (!events) return [] as LiveEvent[];
    return events.slice(0, cursor);
  }, [events, cursor]);

  const tickerRows = useMemo(() => {
    if (seen.length === 0) return [] as LiveEvent[];
    return seen.slice(-TICKER_ROWS).slice().reverse();
  }, [seen]);

  const allAlerts = useMemo(() => {
    return seen.filter((e) => e.alert !== null);
  }, [seen]);

  const recentAlerts = useMemo(() => {
    return allAlerts.slice(-ALERT_ROWS).slice().reverse();
  }, [allAlerts]);

  const currentEvent = seen.length > 0 ? seen[seen.length - 1] : null;
  const populationSize = currentEvent?.population_size ?? 0;
  const isWarming = currentEvent?.warming_up ?? true;
  const isComplete = events !== null && cursor >= events.length;
  const remaining = events ? events.length - cursor : 0;
  const startTime = events && events.length > 0 ? events[0].tx.block_time_s : 0;
  const latestAlertTick = recentAlerts[0]?.alert?.tick ?? null;

  const statusLabel = useMemo(() => {
    if (!events) return "loading";
    if (isComplete) return "complete";
    if (isWarming) {
      const observed = Math.min(populationSize, WARMUP_THRESHOLD);
      return `warming up (${observed} / ${WARMUP_THRESHOLD})`;
    }
    return `live · ${remaining} tx left`;
  }, [events, isComplete, isWarming, populationSize, remaining]);

  if (events === null) {
    return (
      <section className="bg-ink-800 border border-ink-700 rounded-lg p-4">
        <h2 className="text-ink-50 text-xl font-semibold">Live Fraud Tracker</h2>
        <p className="text-ink-500 text-sm mt-1">Loading...</p>
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="bg-ink-800 border border-ink-700 rounded-lg p-4 h-20 animate-pulse"
            />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="bg-ink-800 border border-ink-700 rounded-lg p-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-ink-50 text-xl font-semibold">Live Fraud Tracker</h2>
          <p className="text-ink-500 text-sm mt-1 max-w-2xl">
            Replay of recently-decoded Base x402 settlements. Each tick = 1 tx;
            alerts fire when a wallet crosses the live population&apos;s top-8%
            behavioural composite.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setPaused((p) => !p)}
            disabled={isComplete}
            className="bg-ink-700 hover:bg-ink-700/70 disabled:opacity-40 disabled:cursor-not-allowed text-ink-50 text-sm px-3 py-1.5 rounded-md border border-ink-700"
          >
            {paused ? "Resume" : "Pause"}
          </button>
          <button
            type="button"
            onClick={() => {
              setCursor(0);
              setPaused(false);
            }}
            className="bg-teal-500/15 hover:bg-teal-500/25 text-teal-500 text-sm px-3 py-1.5 rounded-md border border-teal-500/40"
          >
            Restart
          </button>
        </div>
      </div>

      {/* Metric cards */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard label="Tx seen" value={cursor.toString()} />
        <MetricCard label="Wallets observed" value={populationSize.toString()} />
        <MetricCard label="Alerts raised" value={allAlerts.length.toString()} />
        <MetricCard label="Status" value={statusLabel} small />
      </div>

      {isComplete && (
        <div className="mt-3 text-ink-300 text-sm border border-ink-700 rounded-md p-3 bg-ink-900/40">
          stream complete — restart to replay
        </div>
      )}

      {/* Two-column layout */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Last alerts */}
        <div className="bg-ink-800 border border-ink-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-ink-50 text-sm font-semibold uppercase tracking-wide">
              Last alerts
            </h3>
            <span className="text-ink-500 text-xs">{allAlerts.length} total</span>
          </div>
          {recentAlerts.length === 0 ? (
            <div className="text-ink-500 text-sm py-8 text-center">
              No alerts yet. Wallets are still being profiled.
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {recentAlerts.map((event) => {
                const alert = event.alert!;
                const isLatest = alert.tick === latestAlertTick;
                return (
                  <div
                    key={`${alert.tick}-${alert.tx_hash}`}
                    className={`bg-ink-900/60 border border-ink-700 ${
                      tierBorder[alert.tier]
                    } border-l-[3px] rounded-md p-3 ${
                      isLatest ? "animate-flash" : ""
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`${tierBadge[alert.tier]} rounded-full px-2 py-0.5 text-xs font-semibold uppercase tracking-wide`}
                      >
                        {alert.tier}
                      </span>
                      <span className="text-ink-500 text-xs font-mono">
                        score {alert.composite_score.toFixed(2)}
                      </span>
                    </div>
                    <div className="mt-2 text-ink-50 text-sm font-mono">
                      {alert.wallet_short || shortAddr(alert.wallet)}
                    </div>
                    <div className="text-ink-300 text-xs mt-1">
                      {alert.explanation}
                    </div>
                    <div className="mt-2 flex items-center justify-between text-xs">
                      <span className="text-ink-500 font-mono">
                        → {alert.to_addr_short}
                      </span>
                      <span className="text-ink-300 font-mono">
                        {formatUsd(alert.value_usd)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Stream ticker */}
        <div className="bg-ink-800 border border-ink-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-ink-50 text-sm font-semibold uppercase tracking-wide">
              Stream ticker
            </h3>
            <span className="text-ink-500 text-xs">
              {tickerRows.length} / {TICKER_ROWS}
            </span>
          </div>
          {tickerRows.length === 0 ? (
            <div className="text-ink-500 text-sm py-8 text-center">
              Waiting for first transaction...
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-ink-500 text-left">
                    <th className="font-medium pb-2 pr-2">Time</th>
                    <th className="font-medium pb-2 pr-2">Payer</th>
                    <th className="font-medium pb-2 pr-2">Merchant</th>
                    <th className="font-medium pb-2 pr-2 text-right">Amount</th>
                    <th className="font-medium pb-2 pl-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {tickerRows.map((event) => {
                    const elapsed = event.tx.block_time_s - startTime;
                    return (
                      <tr
                        key={`${event.tick}-${event.tx.tx_hash}`}
                        className="border-t border-ink-700/60"
                      >
                        <td className="py-1.5 pr-2 text-ink-300 font-mono">
                          {formatTime(elapsed)}
                        </td>
                        <td className="py-1.5 pr-2 text-ink-300 font-mono">
                          {shortAddr(event.tx.from_addr)}
                        </td>
                        <td className="py-1.5 pr-2 text-ink-300 font-mono">
                          {shortAddr(event.tx.to_addr)}
                        </td>
                        <td className="py-1.5 pr-2 text-ink-50 font-mono text-right">
                          {formatUsd(event.tx.value_usd)}
                        </td>
                        <td className="py-1.5 pl-2">
                          {event.alert ? (
                            <span
                              className={`${tierBadge[event.alert.tier]} rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide`}
                            >
                              Alert
                            </span>
                          ) : null}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function MetricCard({
  label,
  value,
  small = false,
}: {
  label: string;
  value: string;
  small?: boolean;
}) {
  return (
    <div className="bg-ink-800 border border-ink-700 rounded-lg p-4">
      <div className="text-ink-500 text-xs uppercase tracking-wide">{label}</div>
      <div
        className={`text-ink-50 font-semibold mt-1 ${
          small ? "text-base" : "text-2xl"
        }`}
      >
        {value}
      </div>
    </div>
  );
}
