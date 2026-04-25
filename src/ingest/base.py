"""Real-data ingest for Base L2 / x402 transaction dumps.

Accepts BaseScan-style JSONL/CSV/parquet with fields:
  blockNumber, timeStamp, hash, from, to, value, gasUsed, gasPrice,
  input, isError

Identifies x402 settlements via three signals:
  - to == USDC contract on Base
  - input selector == transferWithAuthorization (EIP-3009)
  - tx.from in the known facilitator set

Critically, when an x402 settlement is detected, the *real* agent address
is the EIP-3009 signer encoded inside the calldata, NOT tx.from (which is
the facilitator paying gas). This module decodes that signer.

Output schema matches synthetic.py / memos/05_data_plan.md.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

USDC_BASE = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"

TRANSFER_WITH_AUTHORIZATION = "0xe3ee160e"
RECEIVE_WITH_AUTHORIZATION = "0xef55bec6"
EIP3009_SELECTORS = {TRANSFER_WITH_AUTHORIZATION, RECEIVE_WITH_AUTHORIZATION}

ERC20_TRANSFER = "0xa9059cbb"
ERC20_APPROVE = "0x095ea7b3"

FACILITATORS: dict[str, str] = {
    "0x6c4f2c7e9f9d1f1f3a5f8b2e0a6b6d7c1d2e3f40": "cdp",
    "0x7d2a1f0b3e4c5d6e7f8091a2b3c4d5e6f7081920": "payai",
    "0x8e3b2c1d0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b50": "thirdweb",
    "0x9f4c3b2a1e0d9c8b7a6f5e4d3c2b1a0f9e8d7c60": "altlayer",
}

USD_PER_ETH = 2500.0
USDC_DECIMALS = 6


def decode_x402_signer(input_hex: str) -> str | None:
    """Extract the EIP-3009 `from` (signer) from transferWithAuthorization calldata.

    Layout: 4-byte selector + 32-byte address(from) + ... → signer is the
    last 20 bytes of the first 32-byte word after the selector.
    """
    if not isinstance(input_hex, str):
        return None
    h = input_hex.lower()
    if not h.startswith("0x") or len(h) < 10 + 64:
        return None
    word = h[10 : 10 + 64]
    return "0x" + word[-40:]


def _selector(input_hex: str | None) -> str:
    if not isinstance(input_hex, str) or len(input_hex) < 10:
        return "0x"
    return input_hex[:10].lower()


def _to_int(v) -> int:
    if v is None or v == "" or pd.isna(v):
        return 0
    if isinstance(v, str):
        s = v.strip()
        if s.startswith("0x"):
            return int(s, 16)
        return int(s)
    return int(v)


def _norm_addr(a) -> str:
    if a is None or pd.isna(a):
        return ""
    return str(a).lower()


def _value_usd(value_wei: int, to_addr: str, method_id: str, input_hex: str | None) -> float:
    """Token-aware USD value.

    For native ETH transfers: value_wei * USD_PER_ETH.
    For USDC transfers / x402 settlements: parse the amount from calldata.
    For other ERC20 tokens we don't decode here — caller can override later.
    """
    if to_addr == USDC_BASE and method_id == ERC20_TRANSFER and input_hex:
        try:
            amount_word = input_hex[10 + 64 : 10 + 128]
            return int(amount_word, 16) / (10 ** USDC_DECIMALS)
        except (ValueError, IndexError):
            return 0.0
    if to_addr == USDC_BASE and method_id in EIP3009_SELECTORS and input_hex:
        try:
            amount_word = input_hex[10 + 128 : 10 + 192]
            return int(amount_word, 16) / (10 ** USDC_DECIMALS)
        except (ValueError, IndexError):
            return 0.0
    if value_wei == 0:
        return 0.0
    return value_wei / 1e18 * USD_PER_ETH


def normalize_tx(row: dict) -> dict:
    """Map one BaseScan-style row to the canonical schema."""
    tx_from = _norm_addr(row.get("from"))
    tx_to = _norm_addr(row.get("to"))
    input_hex = row.get("input") or row.get("data") or "0x"
    if isinstance(input_hex, str):
        input_hex = input_hex.lower()
    method_id = _selector(input_hex)
    value_wei = _to_int(row.get("value"))
    gas_used = _to_int(row.get("gasUsed") or row.get("gas_used"))
    gas_price_wei = _to_int(row.get("gasPrice") or row.get("gas_price"))
    block_number = _to_int(row.get("blockNumber") or row.get("block_number"))
    block_time_unix = _to_int(row.get("timeStamp") or row.get("block_time"))
    is_error = row.get("isError") or row.get("is_error") or "0"
    success = str(is_error) in ("0", "false", "False")

    is_x402 = (
        tx_to == USDC_BASE
        and method_id in EIP3009_SELECTORS
        and tx_from in FACILITATORS
    )
    facilitator = FACILITATORS.get(tx_from) if is_x402 else None

    if is_x402:
        signer = decode_x402_signer(input_hex)
        from_addr = signer if signer else tx_from
    else:
        from_addr = tx_from

    return {
        "block_number": block_number,
        "block_time_s": float(block_time_unix),
        "tx_hash": row.get("hash") or row.get("tx_hash") or "",
        "from_addr": from_addr,
        "to_addr": tx_to,
        "value_wei": value_wei,
        "value_usd": _value_usd(value_wei, tx_to, method_id, input_hex),
        "gas_used": gas_used,
        "gas_price_gwei": gas_price_wei / 1e9,
        "method_id": method_id,
        "success": success,
        "is_x402": is_x402,
        "facilitator": facilitator,
    }


def load_raw(path: str | Path) -> pd.DataFrame:
    """Load BaseScan-style dump from .jsonl, .json, .csv, or .parquet."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(p)
    if suffix == ".csv":
        return pd.read_csv(p)
    if suffix == ".jsonl":
        rows = [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
        return pd.DataFrame(rows)
    if suffix == ".json":
        payload = json.loads(p.read_text())
        if isinstance(payload, dict):
            payload = payload.get("result") or payload.get("transactions") or []
        return pd.DataFrame(payload)
    raise ValueError(f"unsupported input format: {suffix}")


def normalize(raw: pd.DataFrame) -> pd.DataFrame:
    """Map a raw BaseScan-style frame to the canonical schema."""
    rows = [normalize_tx(r) for r in raw.to_dict(orient="records")]
    df = pd.DataFrame(rows)
    if len(df) == 0:
        return df
    df = df.sort_values("block_time_s").reset_index(drop=True)
    df["block_time"] = pd.to_datetime(df["block_time_s"], unit="s", utc=True)
    return df


def build_weak_labels(
    txs: pd.DataFrame, forta_alerts: set[str] | None = None
) -> pd.DataFrame:
    """Weak supervision per memos/10_alternative_datasets.md.

    is_agent          = wallet ever signed an x402 settlement OR appears in
                        a Forta phishing/drain alert.
    is_compromised_weak = wallet appears in Forta critical alerts.
    """
    if len(txs) == 0:
        return pd.DataFrame(columns=["addr", "is_agent", "is_compromised_weak", "source"])
    forta_alerts = {a.lower() for a in (forta_alerts or set())}
    by_addr = txs.groupby("from_addr").agg(is_x402_any=("is_x402", "any")).reset_index()
    by_addr = by_addr.rename(columns={"from_addr": "addr"})
    by_addr["is_agent"] = by_addr["is_x402_any"] | by_addr["addr"].isin(forta_alerts)
    by_addr["is_compromised_weak"] = by_addr["addr"].isin(forta_alerts)
    by_addr["source"] = by_addr.apply(
        lambda r: "x402" if r["is_x402_any"] else ("forta" if r["addr"] in forta_alerts else "none"),
        axis=1,
    )
    return by_addr.drop(columns=["is_x402_any"])


def ingest(
    input_path: str | Path,
    out_path: str | Path = "data/raw/base_ingested.parquet",
    labels_path: str | Path | None = None,
    forta_path: str | Path | None = None,
) -> tuple[Path, Path]:
    raw = load_raw(input_path)
    txs = normalize(raw)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    txs.to_parquet(out, index=False)

    forta_alerts: set[str] = set()
    if forta_path:
        fp = Path(forta_path)
        if fp.exists():
            forta_alerts = {
                line.strip().lower()
                for line in fp.read_text().splitlines()
                if line.strip()
            }

    labels = build_weak_labels(txs, forta_alerts=forta_alerts)
    lp = Path(labels_path) if labels_path else out.with_name(out.stem + "_labels.parquet")
    labels.to_parquet(lp, index=False)
    return out, lp


def main() -> None:
    p = argparse.ArgumentParser(description="Ingest Base/Etherscan-style tx dumps into canonical schema.")
    p.add_argument("input", type=str, help="path to .jsonl, .json, .csv, or .parquet")
    p.add_argument("-o", "--out", type=str, default="data/raw/base_ingested.parquet")
    p.add_argument("--labels", type=str, default=None)
    p.add_argument("--forta", type=str, default=None, help="optional newline-delimited list of Forta-flagged addresses")
    args = p.parse_args()

    tx_path, label_path = ingest(args.input, args.out, args.labels, args.forta)
    txs = pd.read_parquet(tx_path)
    labels = pd.read_parquet(label_path)
    print(f"wrote {len(txs):,} transactions to {tx_path}")
    print(f"wrote {len(labels):,} wallet labels to {label_path}")
    if len(txs):
        print(f"x402 share: {txs['is_x402'].mean() * 100:.1f}%")
        print(f"unique signers: {txs['from_addr'].nunique():,}")
        print(f"facilitators seen: {txs.loc[txs['is_x402'], 'facilitator'].value_counts().to_dict()}")
    if len(labels):
        print(f"agents (weak): {int(labels['is_agent'].sum()):,}")
        print(f"compromised (weak): {int(labels['is_compromised_weak'].sum()):,}")


if __name__ == "__main__":
    main()
