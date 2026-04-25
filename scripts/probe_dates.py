"""Probe daily x402 tx counts around snapshot anchor dates.

Used to size the snapshot windows in pull_dune.py — early dates have ~5 tx/day,
recent dates have >100k/day, so window sizes must be adapted per anchor.
"""
import json
import os
import sys
import time

import requests

API = "https://api.dune.com/api/v1"
key = os.environ.get("DUNE_API_KEY")
if not key:
    sys.exit("DUNE_API_KEY env var not set")
H = {"X-Dune-API-Key": key, "Content-Type": "application/json"}

USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
SEL = "0xe3ee160e"  # transferWithAuthorization

sql = f"""
WITH dates AS (
  SELECT date_trunc('day', block_time) AS day, count(*) AS tx_count
  FROM base.transactions
  WHERE "to" = {USDC}
    AND bytearray_substring(data, 1, 4) = {SEL}
    AND success = true
    AND (
      block_time BETWEEN timestamp '2025-06-01' AND timestamp '2025-06-30'
      OR block_time BETWEEN timestamp '2025-10-01' AND timestamp '2025-10-31'
      OR block_time BETWEEN timestamp '2026-01-15' AND timestamp '2026-01-25'
      OR block_time BETWEEN timestamp '2026-04-22' AND timestamp '2026-04-25'
    )
  GROUP BY 1
)
SELECT day, tx_count FROM dates ORDER BY day
"""

r = requests.post(f"{API}/sql/execute", headers=H, json={"sql": sql})
eid = r.json()["execution_id"]
print(f"eid={eid}")

while True:
    s = requests.get(f"{API}/execution/{eid}/status", headers=H).json()
    if s["state"] == "QUERY_STATE_COMPLETED":
        break
    if s["state"].startswith("QUERY_STATE_") and s["state"] not in (
        "QUERY_STATE_PENDING",
        "QUERY_STATE_EXECUTING",
    ):
        print(json.dumps(s, indent=2))
        sys.exit(1)
    print(f"  {s['state']}")
    time.sleep(4)

res = requests.get(f"{API}/execution/{eid}/results", headers=H).json()
print(f"\nrows: {len(res['result']['rows'])}")
for row in res["result"]["rows"]:
    print(f"  {row['day'][:10]}  {row['tx_count']:>10,}")
