"""Inline-execute Dune queries: facilitators, x402 traffic, baseline, snapshots.

Two-key support: set DUNE_API_KEY (and optionally DUNE_API_KEY_2) — script
auto-rotates on quota errors (HTTP 402/429).

Outputs raw CSVs to data/raw/. Convert to the canonical x402_*.parquet
naming with a short pandas script if needed.

Usage:
  python scripts/pull_dune.py live                  # current x402 + baseline
  python scripts/pull_dune.py snapshots             # 4 historical snapshots
  python scripts/pull_dune.py both
  python scripts/pull_dune.py snapshots --snapshot_row_limit 300
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import requests

API_BASE = "https://api.dune.com/api/v1"

USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
SELECTOR = "0xe3ee160e"  # transferWithAuthorization

OUT = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------------
# Key pool with auto-fallback
# ----------------------------------------------------------------------------

@dataclass
class KeyPool:
    keys: list[tuple[str, str]] = field(default_factory=list)  # (label, key)
    cursor: int = 0

    @classmethod
    def from_env(cls) -> "KeyPool":
        keys = []
        for var in ["DUNE_API_KEY", "DUNE_API_KEY_2", "DUNE_API_KEY_3"]:
            v = os.environ.get(var)
            if v:
                keys.append((var, v))
        if not keys:
            sys.exit("No keys: set DUNE_API_KEY (and optionally DUNE_API_KEY_2)")
        print(f"[keys] loaded {len(keys)} key(s): {[k[0] for k in keys]}")
        return cls(keys=keys)

    def headers(self) -> dict:
        label, key = self.keys[self.cursor]
        return {"X-Dune-API-Key": key, "Content-Type": "application/json"}

    def label(self) -> str:
        return self.keys[self.cursor][0]

    def rotate(self) -> bool:
        self.cursor += 1
        if self.cursor >= len(self.keys):
            return False
        print(f"[keys] rotated -> {self.keys[self.cursor][0]}")
        return True


# ----------------------------------------------------------------------------
# Execute / wait / fetch
# ----------------------------------------------------------------------------

def execute(pool: KeyPool, sql: str) -> tuple[str, str]:
    """Returns (execution_id, key_label_used)."""
    while True:
        r = requests.post(f"{API_BASE}/sql/execute", headers=pool.headers(),
                          json={"sql": sql}, timeout=30)
        if r.status_code == 200:
            eid = r.json().get("execution_id")
            if not eid:
                sys.exit(f"no execution_id in: {r.text}")
            return eid, pool.label()
        if r.status_code in (402, 429):
            print(f"[{pool.label()}] quota/rate {r.status_code}: {r.text[:200]}")
            if not pool.rotate():
                sys.exit("All keys exhausted")
            continue
        sys.exit(f"execute error {r.status_code}: {r.text}")


def wait(pool: KeyPool, execution_id: str, max_s: int = 600, poll_s: int = 5) -> dict:
    waited = 0
    while waited < max_s:
        r = requests.get(f"{API_BASE}/execution/{execution_id}/status",
                         headers=pool.headers(), timeout=15)
        r.raise_for_status()
        body = r.json()
        state = body["state"]
        if state == "QUERY_STATE_COMPLETED":
            return body
        if state in {"QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED", "QUERY_STATE_EXPIRED"}:
            sys.exit(f"failed: {json.dumps(body, indent=2)}")
        print(f"    state={state} t+{waited}s")
        time.sleep(poll_s)
        waited += poll_s
    sys.exit(f"timeout {max_s}s")


def fetch_csv(pool: KeyPool, execution_id: str, out_path: Path) -> int:
    r = requests.get(f"{API_BASE}/execution/{execution_id}/results/csv",
                     headers=pool.headers(), timeout=120)
    r.raise_for_status()
    out_path.write_bytes(r.content)
    return max(r.text.count("\n") - 1, 0)


def run_query(pool: KeyPool, name: str, sql: str) -> dict:
    print(f"\n=== {name} ===")
    eid, used = execute(pool, sql)
    print(f"  execution_id={eid} via {used}")
    status = wait(pool, eid)
    meta = status.get("result_metadata", {}) or {}
    rc = meta.get("total_row_count", 0)
    dp = meta.get("datapoint_count", 0)
    ms = meta.get("execution_time_millis", 0)
    csv_path = OUT / f"{name}.csv"
    nrows = fetch_csv(pool, eid, csv_path)
    print(f"  rows={rc}, datapoints={dp}, exec_time={ms}ms -> {csv_path}")
    return {"execution_id": eid, "key": used, "rows": rc,
            "datapoints": dp, "exec_ms": ms, "csv": str(csv_path)}


# ----------------------------------------------------------------------------
# SQL builders
# ----------------------------------------------------------------------------

def sql_facilitators(window_days: int = 7) -> str:
    return f"""
        SELECT "from" AS facilitator, count(*) AS tx_count
        FROM base.transactions
        WHERE "to" = {USDC_BASE}
          AND bytearray_substring(data, 1, 4) = {SELECTOR}
          AND block_time > now() - interval '{window_days}' day
          AND success = true
        GROUP BY 1 ORDER BY tx_count DESC LIMIT 20
    """


def sql_x402_live(window_min: int, row_limit: int) -> str:
    return f"""
        WITH x402_txs AS (
          SELECT hash, block_time, "from" AS facilitator, gas_price, gas_used
          FROM base.transactions
          WHERE "to" = {USDC_BASE}
            AND bytearray_substring(data, 1, 4) = {SELECTOR}
            AND block_time > now() - interval '{window_min}' minute
            AND success = true
          LIMIT {row_limit}
        )
        SELECT
          x.block_time,
          tr."from" AS payer,
          tr."to" AS merchant,
          CAST(tr.value AS DOUBLE) / 1e6 AS value_usd,
          x.facilitator,
          CAST(x.gas_price AS DOUBLE) / 1e9 AS gas_price_gwei,
          x.gas_used
        FROM x402_txs x
        INNER JOIN erc20_base.evt_Transfer tr ON x.hash = tr.evt_tx_hash
        WHERE tr.contract_address = {USDC_BASE}
          AND tr.evt_block_time > now() - interval '{window_min}' minute
        ORDER BY x.block_time DESC
    """


def sql_baseline(window_min: int, row_limit: int) -> str:
    return f"""
        SELECT block_time, "from" AS payer, "to" AS merchant,
               CAST(value AS DOUBLE) / 1e18 AS value_eth,
               CAST(gas_price AS DOUBLE) / 1e9 AS gas_price_gwei,
               gas_used
        FROM base.transactions
        WHERE block_time > now() - interval '{window_min}' minute
          AND "to" != {USDC_BASE}
          AND value > 0
          AND success = true
        ORDER BY block_time DESC
        LIMIT {row_limit}
    """


def sql_snapshot(start_iso: str, end_iso: str, row_limit: int,
                 include_gas: bool) -> str:
    """Historical x402 snapshot. Cuts cost by joining to evt_Transfer with
    matching partition filter on evt_block_time."""
    extra = """,
      t."from" AS facilitator,
      CAST(t.gas_price AS DOUBLE) / 1e9 AS gas_price_gwei,
      t.gas_used""" if include_gas else ""
    return f"""
        WITH x402_txs AS (
          SELECT hash, block_time, "from", gas_price, gas_used
          FROM base.transactions
          WHERE "to" = {USDC_BASE}
            AND bytearray_substring(data, 1, 4) = {SELECTOR}
            AND block_time BETWEEN timestamp '{start_iso}' AND timestamp '{end_iso}'
            AND success = true
          LIMIT {row_limit}
        )
        SELECT
          t.block_time,
          tr."from" AS payer,
          tr."to" AS merchant,
          CAST(tr.value AS DOUBLE) / 1e6 AS value_usd{extra}
        FROM x402_txs t
        INNER JOIN erc20_base.evt_Transfer tr ON t.hash = tr.evt_tx_hash
        WHERE tr.contract_address = {USDC_BASE}
          AND tr.evt_block_time BETWEEN timestamp '{start_iso}' AND timestamp '{end_iso}'
        ORDER BY t.block_time DESC
    """


# Snapshot presets. (start_iso, end_iso, label, description) — windows widened
# adaptively because x402 daily volume spans 6 orders of magnitude across these
# dates (5 tx/day in 2025-06, ~140k tx/day in 2026-04).
SNAPSHOTS = [
    ("2025-06-01 00:00:00", "2025-06-30 23:59:59",
        "early_adopters",  "Full June 2025 (manual era, ~5 tx/day)"),
    ("2025-10-15 00:00:00", "2025-10-15 23:59:59",
        "post_linux_fdn",  "2025-10-15 full day (~90 tx)"),
    ("2026-01-20 12:00:00", "2026-01-20 13:00:00",
        "post_stripe",     "2026-01-20 noon UTC, 1h (~500 tx)"),
    ("2026-04-24 12:00:00", "2026-04-24 13:00:00",
        "current",         "2026-04-24 noon UTC, 1h (~5,800 tx, capped)"),
]


def render_snapshot(start_iso: str, end_iso: str, row_limit: int,
                    include_gas: bool) -> str:
    return sql_snapshot(start_iso, end_iso, row_limit, include_gas)


# ----------------------------------------------------------------------------
# Strategies
# ----------------------------------------------------------------------------

def run_live(pool: KeyPool, args) -> dict:
    queries = {
        "facilitators": sql_facilitators(args.window_days),
        "x402_traffic": sql_x402_live(args.window_minutes, args.row_limit_x402),
        "baseline":     sql_baseline(args.window_minutes, args.row_limit_baseline),
    }
    return {name: run_query(pool, name, sql) for name, sql in queries.items()}


def run_snapshots(pool: KeyPool, args) -> dict:
    out = {}
    for start_iso, end_iso, label, descr in SNAPSHOTS:
        print(f"\n--- snapshot {label} [{start_iso} -> {end_iso}]: {descr} ---")
        sql = render_snapshot(start_iso, end_iso,
                              args.snapshot_row_limit, args.include_gas)
        try:
            out[label] = run_query(pool, f"snapshot_{label}", sql)
        except SystemExit as e:
            print(f"  ! {label} failed: {e}")
            out[label] = {"error": str(e)}
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("strategy", choices=["live", "snapshots", "both"], default="live", nargs="?")
    p.add_argument("--window_days", type=int, default=7)
    p.add_argument("--window_minutes", type=int, default=60)
    p.add_argument("--row_limit_x402", type=int, default=3000)
    p.add_argument("--row_limit_baseline", type=int, default=2000)
    p.add_argument("--snapshot_row_limit", type=int, default=300)
    p.add_argument("--snapshot_duration_minutes", type=int, default=60)
    p.add_argument("--include_gas", action="store_true",
                   help="Include gas cols in snapshots (~2x datapoints)")
    args = p.parse_args()

    pool = KeyPool.from_env()
    summary = {}
    if args.strategy in ("live", "both"):
        summary["live"] = run_live(pool, args)
    if args.strategy in ("snapshots", "both"):
        summary["snapshots"] = run_snapshots(pool, args)

    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\n=== summary -> {OUT / 'summary.json'} ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
