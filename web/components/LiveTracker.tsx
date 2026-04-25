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

type Subscores = Record<SubscoreKey, number | null>;

type LiveAlert = {
  tick: number;
  wallet: string;
  wallet_short: string;
  overall_action_risk: number;
  composite_score: number;
  tier: Tier;
  subscores: Record<string, number>;
  top_factor_name: string;
  top_factor_value: number;
  top_factors: Array<{ name: string; label: string; score: number }>;
  explanation: string;
  value_usd: number;
  tx_hash: string;
  to_addr_short: string;
};

type LiveEvent = {
  tick: number;
  tx: {
    from_addr: string;
    to_addr: string;
    value_usd: number;
    tx_hash: string;
    block_time_s: number;
    method_id: string;
    prompt_injection_flag: boolean;
  };
  population_size: number;
  warming_up: boolean;
  score: number | null;
  tier: Tier | null;
  subscores: Subscores;
  alert: LiveAlert | null;
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

type Meta = {
  built_at: string;
  trend_rows: number;
  scenarios: ScenarioMeta[];
  headline: {
    median_compression: number;
    volume_growth: number;
    rf_accuracy: number;
    feature_mi_pass_rate: number;
  };
};

const TICKER_ROWS = 12;
const ALERT_ROWS = 4;
const WARMUP_THRESHOLD = 25;

const SUBSCORE_ORDER: SubscoreKey[] = [
  "agent_likeness_score",
  "drift_score",
  "coordination_score",
  "policy_violation_score",
  "counterparty_risk_score",
  "prompt_injection_score",
];

const SUBSCORE_LABEL: Record<SubscoreKey, string> = {
  agent_likeness_score: "Agent-likeness",
  drift_score: "Behavioural drift",
  coordination_score: "Peer coordination",
  policy_violation_score: "Policy violation",
  counterparty_risk_score: "Counterparty risk",
  prompt_injection_score: "Prompt-injection",
};

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

type Decision = "Allow" | "Review" | "Block";

const decisionBadge: Record<Decision, string> = {
  Allow: "bg-risk-low/15 text-risk-low",
  Review: "bg-risk-high/15 text-risk-high",
  Block: "bg-risk-critical/15 text-risk-critical",
};

function decideAction(event: LiveEvent): Decision {
  const alert = event.alert;
  if (!alert) return "Allow";
  if (alert.tier === "critical" || alert.top_factor_value >= 90) return "Block";
  return "Review";
}

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
  const [meta, setMeta] = useState<Meta | null>(null);
  const [scenarioKey, setScenarioKey] = useState<string | null>(null);
  const [events, setEvents] = useState<LiveEvent[] | null>(null);
  const [cursor, setCursor] = useState(0);
  const [paused, setPaused] = useState(false);

  // Fetch meta.json on mount.
  useEffect(() => {
    let cancelled = false;
    fetch("/data/meta.json")
      .then((r) => r.json())
      .then((data: Meta) => {
        if (cancelled) return;
        setMeta(data);
        const preferred = data.scenarios.find((s) => s.key === "base_x402");
        const initial = preferred?.key ?? data.scenarios[0]?.key ?? null;
        setScenarioKey(initial);
      })
      .catch(() => {
        if (!cancelled) setMeta({ built_at: "", trend_rows: 0, scenarios: [], headline: { median_compression: 0, volume_growth: 0, rf_accuracy: 0, feature_mi_pass_rate: 0 } });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Fetch the selected scenario's events.
  useEffect(() => {
    if (!scenarioKey) return;
    let cancelled = false;
    setEvents(null);
    setCursor(0);
    setPaused(false);
    fetch(`/data/scenarios/${scenarioKey}/events.json`)
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
  }, [scenarioKey]);

  useEffect(() => {
    if (!events || paused) return;
    if (cursor >= events.length) return;
    const id = setInterval(() => {
      setCursor((c) => {
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

  const allAlerts = useMemo(() => seen.filter((e) => e.alert !== null), [seen]);
  const recentAlerts = useMemo(() => allAlerts.slice(-ALERT_ROWS).slice().reverse(), [allAlerts]);

  const currentEvent = seen.length > 0 ? seen[seen.length - 1] : null;
  const populationSize = currentEvent?.population_size ?? 0;
  const isWarming = currentEvent?.warming_up ?? true;
  const isComplete = events !== null && cursor >= events.length;
  const remaining = events ? events.length - cursor : 0;
  const startTime = events && events.length > 0 ? events[0].tx.block_time_s : 0;
  const latestAlertTick = recentAlerts[0]?.alert?.tick ?? null;

  const selectedScenario = useMemo(() => {
    if (!meta || !scenarioKey) return null;
    return meta.scenarios.find((s) => s.key === scenarioKey) ?? null;
  }, [meta, scenarioKey]);

  const statusLabel = useMemo(() => {
    if (!events) return "loading";
    if (isComplete) return "complete";
    if (isWarming) {
      const observed = Math.min(populationSize, WARMUP_THRESHOLD);
      return `warming up (${observed} / ${WARMUP_THRESHOLD})`;
    }
    return `live · ${remaining} tx left`;
  }, [events, isComplete, isWarming, populationSize, remaining]);

  if (meta === null) {
    return (
      <section className="bg-ink-800 border border-ink-700 rounded-lg p-4">
        <h2 className="text-ink-50 text-xl font-semibold">Live Action Risk</h2>
        <p className="text-ink-500 text-sm mt-1">Loading...</p>
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-ink-800 border border-ink-700 rounded-lg p-4 h-20 animate-pulse" />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="bg-ink-800 border border-ink-700 rounded-lg p-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-ink-50 text-xl font-semibold">Live Action Risk</h2>
          <p className="text-ink-500 text-sm mt-1 max-w-2xl">
            Behavioural risk stream over real x402 settlements (or synthetic scenarios). Each
            tick = 1 tx; an alert fires when a wallet&apos;s overall action risk enters the live
            top-8% <strong className="text-ink-300">or</strong> any sub-score crosses 75 / 100.
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <select
            value={scenarioKey ?? ""}
            onChange={(e) => setScenarioKey(e.target.value)}
            className="bg-ink-900 border border-ink-700 text-ink-50 text-sm px-3 py-1.5 rounded-md focus:outline-none focus:border-teal-500"
            title={selectedScenario?.description ?? ""}
          >
            {meta.scenarios.map((s) => (
              <option key={s.key} value={s.key} title={s.description}>
                {s.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => setPaused((p) => !p)}
            disabled={isComplete || events === null}
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

      {selectedScenario && (
        <p className="text-ink-500 text-xs mt-2">{selectedScenario.description}</p>
      )}

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
            <h3 className="text-ink-50 text-sm font-semibold uppercase tracking-wide">Last alerts</h3>
            <span className="text-ink-500 text-xs">{allAlerts.length} total</span>
          </div>
          {recentAlerts.length === 0 ? (
            <div className="text-ink-500 text-sm py-8 text-center">
              {events === null ? "Loading scenario..." : "No alerts yet. Wallets are still being profiled."}
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {recentAlerts.map((event) => {
                const alert = event.alert!;
                const isLatest = alert.tick === latestAlertTick;
                return (
                  <div
                    key={`${alert.tick}-${alert.tx_hash}`}
                    className={`bg-ink-900/60 border border-ink-700 ${tierBorder[alert.tier]} border-l-[3px] rounded-md p-3 ${isLatest ? "animate-flash" : ""}`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`${tierBadge[alert.tier]} rounded-full px-2 py-0.5 text-xs font-semibold uppercase tracking-wide`}
                      >
                        {alert.tier}
                      </span>
                      <span className="text-ink-500 text-xs font-mono">
                        risk {alert.overall_action_risk.toFixed(2)}
                      </span>
                    </div>
                    <div className="mt-2 text-ink-50 text-sm font-mono">
                      {alert.wallet_short || shortAddr(alert.wallet)}
                    </div>

                    {/* Top factors as badges */}
                    {alert.top_factors && alert.top_factors.length > 0 && (
                      <div className="mt-2 text-ink-300 text-xs flex flex-wrap gap-x-1 gap-y-0.5">
                        {alert.top_factors.slice(0, 3).map((f, idx) => (
                          <span key={f.name}>
                            <span className="text-ink-50">{f.label}</span>{" "}
                            <span className="text-ink-300 font-mono">{f.score.toFixed(0)}</span>
                            {idx < Math.min(2, alert.top_factors.length - 1) && (
                              <span className="text-ink-500"> · </span>
                            )}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Sub-score mini-bars */}
                    <div className="mt-2 flex flex-col gap-1">
                      {SUBSCORE_ORDER.map((key) => {
                        const raw = alert.subscores[key];
                        const score = typeof raw === "number" ? raw : 0;
                        const isTop = alert.top_factor_name === key;
                        const width = `${Math.max(0, Math.min(100, score))}%`;
                        return (
                          <div key={key} className="flex items-center gap-2 text-[10px]">
                            <div className="w-24 text-ink-300 shrink-0">{SUBSCORE_LABEL[key]}</div>
                            <div className="flex-1 h-1.5 bg-ink-900 rounded-sm overflow-hidden">
                              <div
                                className={`h-full ${isTop ? "bg-teal-500" : "bg-ink-500"}`}
                                style={{ width }}
                              />
                            </div>
                            <div
                              className={`w-7 text-right font-mono ${isTop ? "text-teal-500" : "text-ink-300"}`}
                            >
                              {score.toFixed(0)}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    <div className="mt-2 text-ink-500 text-xs">{alert.explanation}</div>

                    <div className="mt-2 flex items-center justify-between text-xs">
                      <span className="text-ink-500 font-mono">→ {alert.to_addr_short}</span>
                      <span className="text-ink-300 font-mono">{formatUsd(alert.value_usd)}</span>
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
            <h3 className="text-ink-50 text-sm font-semibold uppercase tracking-wide">Stream ticker</h3>
            <span className="text-ink-500 text-xs">
              {tickerRows.length} / {TICKER_ROWS}
            </span>
          </div>
          {tickerRows.length === 0 ? (
            <div className="text-ink-500 text-sm py-8 text-center">
              {events === null ? "Loading scenario..." : "Waiting for first transaction..."}
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
                    <th className="font-medium pb-2 pl-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {tickerRows.map((event) => {
                    const elapsed = event.tx.block_time_s - startTime;
                    const decision = decideAction(event);
                    return (
                      <tr key={`${event.tick}-${event.tx.tx_hash}`} className="border-t border-ink-700/60">
                        <td className="py-1.5 pr-2 text-ink-300 font-mono">{formatTime(elapsed)}</td>
                        <td className="py-1.5 pr-2 text-ink-300 font-mono">{shortAddr(event.tx.from_addr)}</td>
                        <td className="py-1.5 pr-2 text-ink-300 font-mono">{shortAddr(event.tx.to_addr)}</td>
                        <td className="py-1.5 pr-2 text-ink-50 font-mono text-right">{formatUsd(event.tx.value_usd)}</td>
                        <td className="py-1.5 pl-2">
                          <span
                            className={`${decisionBadge[decision]} rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide`}
                          >
                            {decision}
                          </span>
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
      <div className={`text-ink-50 font-semibold mt-1 ${small ? "text-base" : "text-2xl"}`}>{value}</div>
    </div>
  );
}
