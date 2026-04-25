"""Probe how fresh base.transactions is on Dune."""
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

sql = """
SELECT
  max(block_time)            AS max_time,
  date_diff('second', max(block_time), now()) AS lag_seconds,
  count(*)                    AS n_rows
FROM base.transactions
WHERE block_time > now() - interval '2' hour
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
    time.sleep(3)

res = requests.get(f"{API}/execution/{eid}/results", headers=H).json()
print(json.dumps(res["result"]["rows"], indent=2))
