"""Collect no-key public x402 data.

Easy sources:
  - x402.watch facilitator directory HTML
  - Facilitator /supported endpoints
  - Base Blockscout account txlist API

The most useful real-data path today is facilitator signer txs to Base USDC.
For x402 v2 EIP-3009 payments, the signer calls USDC with a payload shaped like
transferWithAuthorization(from, to, value, validAfter, validBefore, nonce, ...).
This module decodes those calldata fields and emits both raw rows and a
pipeline-compatible transaction table.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pandas as pd
import requests


X402_WATCH_FACILITATORS = "https://www.x402.watch/facilitators"
X402_WATCH_COINBASE = "https://x402.watch/facilitator/coinbase"
OPENX402_FACILITATOR = "https://facilitator.openx402.ai"
BASE_BLOCKSCOUT_API = "https://base.blockscout.com/api"
BASE_CHAIN_ID = "eip155:8453"
BASE_USDC = "0x833589fcD6edB6E08f4c7C32D4f71b54bdA02913".lower()
TRANSFER_WITH_AUTH_SELECTOR = "0xe3ee160e"
REQUEST_TIMEOUT_S = 25


@dataclass
class FetchResult:
    ok: bool
    status_code: int
    text: str
    url: str


def _get(url: str, **params: Any) -> FetchResult:
    try:
        resp = requests.get(url, params=params or None, timeout=REQUEST_TIMEOUT_S)
        return FetchResult(resp.ok, resp.status_code, resp.text, resp.url)
    except Exception as exc:
        return FetchResult(False, 0, str(exc), url)


def _get_json(url: str, **params: Any) -> tuple[dict[str, Any] | list[Any] | None, FetchResult]:
    result = _get(url, **params)
    if not result.ok:
        return None, result
    try:
        return json.loads(result.text), result
    except json.JSONDecodeError:
        return None, result


def _normalise_url(url: str) -> str:
    url = url.strip().rstrip("<").rstrip("/")
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


def scrape_x402_watch_facilitators() -> pd.DataFrame:
    """Scrape the public x402.watch directory into a light facilitator table."""
    page = _get(X402_WATCH_FACILITATORS)
    if not page.ok:
        return pd.DataFrame()

    rows = []
    row_pattern = re.compile(
        r'<a class="fac-name" href="/facilitator/(?P<slug>[^"]+)">(?P<name>.*?)</a>'
        r'.*?<span class="url mono" title="(?P<url>https://[^"]+)">',
        flags=re.DOTALL,
    )
    for match in row_pattern.finditer(page.text):
        url = _normalise_url(match.group("url"))
        if not url:
            continue
        slug = match.group("slug")
        name = re.sub(r"<.*?>", "", match.group("name")).strip()
        host = urlparse(url).netloc
        rows.append({
            "source": "x402.watch",
            "name": name,
            "slug": slug,
            "facilitator_url": url,
            "host": host,
            "supports_base_hint": "network#base" in page.text,
        })
    # Make sure Coinbase appears even when the list truncates in a changed page.
    if not any("coinbase" in r["host"] for r in rows):
        rows.append({
            "source": "x402.watch",
            "name": "Coinbase",
            "slug": "coinbase",
            "facilitator_url": "https://facilitator.cdp.coinbase.com",
            "host": "facilitator.cdp.coinbase.com",
            "supports_base_hint": True,
        })
    out = pd.DataFrame(rows).drop_duplicates(subset=["facilitator_url"])
    out["known_slug_count_on_page"] = len(set(re.findall(r'href="/facilitator/([^"]+)"', page.text)))
    return out.sort_values("facilitator_url").reset_index(drop=True)


def scrape_coinbase_addresses() -> pd.DataFrame:
    """Coinbase facilitator addresses exposed on x402.watch."""
    page = _get(X402_WATCH_COINBASE)
    addrs = sorted(set(a.lower() for a in re.findall(r"0x[a-fA-F0-9]{40}", page.text)))
    rows = []
    for address in addrs:
        rows.append({
            "source": "x402.watch/facilitator/coinbase",
            "facilitator": "coinbase",
            "network": BASE_CHAIN_ID,
            "address": address,
            "address_role": "facilitator_address_page_match",
        })
    return pd.DataFrame(rows)


def probe_supported(facilitators: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Call /supported for each facilitator URL where it looks plausible."""
    support_rows = []
    address_rows = []
    urls = facilitators["facilitator_url"].dropna().unique().tolist()
    if OPENX402_FACILITATOR not in urls:
        urls.append(OPENX402_FACILITATOR)

    for url in sorted(urls):
        supported_url = f"{url.rstrip('/')}/supported"
        payload, result = _get_json(supported_url)
        row = {
            "facilitator_url": url,
            "supported_url": supported_url,
            "ok": bool(payload is not None),
            "status_code": result.status_code,
            "network_count": 0,
            "extension_count": 0,
            "raw_error": "" if payload is not None else result.text[:240],
        }
        if isinstance(payload, dict):
            kinds = payload.get("kinds") or []
            row["network_count"] = len(kinds)
            row["extension_count"] = len(payload.get("extensions") or [])
            for kind in kinds:
                extra = kind.get("extra") or {}
                support_rows.append({
                    "facilitator_url": url,
                    "network": kind.get("network"),
                    "x402_version": kind.get("x402Version"),
                    "scheme": kind.get("scheme"),
                    "asset": str(extra.get("asset", "")).lower(),
                    "asset_name": extra.get("name", ""),
                    "asset_transfer_method": extra.get("assetTransferMethod", ""),
                })
            for network, signers in (payload.get("signers") or {}).items():
                for signer in signers:
                    if isinstance(signer, str) and signer.startswith("0x"):
                        address_rows.append({
                            "source": f"{url}/supported",
                            "facilitator": urlparse(url).netloc,
                            "network": network,
                            "address": signer.lower(),
                            "address_role": "signer",
                        })
        support_rows.append(row | {"record_type": "probe"})
        time.sleep(0.15)

    support = pd.DataFrame(support_rows)
    addresses = pd.DataFrame(address_rows)
    return support, addresses


def fetch_blockscout_txlist(address: str, offset: int = 200) -> pd.DataFrame:
    payload, result = _get_json(
        BASE_BLOCKSCOUT_API,
        module="account",
        action="txlist",
        address=address,
        page=1,
        offset=offset,
        sort="desc",
    )
    if not isinstance(payload, dict) or payload.get("message") != "OK":
        return pd.DataFrame([{
            "watched_address": address.lower(),
            "fetch_error": result.text[:300],
        }])
    rows = payload.get("result") or []
    df = pd.DataFrame(rows)
    if len(df) == 0:
        return df
    df["watched_address"] = address.lower()
    df["source"] = "base.blockscout.txlist"
    return df


def _word_to_address(word: str) -> str:
    return "0x" + word[-40:].lower()


def _word_to_int(word: str) -> int:
    return int(word, 16)


def decode_transfer_with_authorization(input_hex: str) -> dict[str, Any]:
    """Decode the first EIP-3009 transferWithAuthorization fields."""
    if not isinstance(input_hex, str) or not input_hex.startswith(TRANSFER_WITH_AUTH_SELECTOR):
        return {}
    body = input_hex[10:]
    words = [body[i:i + 64] for i in range(0, len(body), 64)]
    if len(words) < 6:
        return {}
    return {
        "decoded_method": "transferWithAuthorization",
        "payer_addr": _word_to_address(words[0]),
        "recipient_addr": _word_to_address(words[1]),
        "amount_raw": _word_to_int(words[2]),
        "amount_usdc": _word_to_int(words[2]) / 1_000_000.0,
        "valid_after": _word_to_int(words[3]),
        "valid_before": _word_to_int(words[4]),
        "authorization_nonce": "0x" + words[5],
    }


def normalise_x402_txs(raw: pd.DataFrame) -> pd.DataFrame:
    if len(raw) == 0:
        return pd.DataFrame()
    txs = raw.copy()
    for col in ["from", "to", "input", "hash", "methodId", "timeStamp", "blockNumber", "gasUsed", "gasPrice", "value"]:
        if col not in txs.columns:
            txs[col] = None
    decoded = txs["input"].apply(decode_transfer_with_authorization).apply(pd.Series)
    out = pd.concat([txs.reset_index(drop=True), decoded.reset_index(drop=True)], axis=1)
    out["is_x402_eip3009"] = (
        out["to"].astype(str).str.lower().eq(BASE_USDC)
        & out["methodId"].astype(str).str.lower().eq(TRANSFER_WITH_AUTH_SELECTOR)
        & out["payer_addr"].notna()
    )
    out["facilitator_addr"] = out["from"].astype(str).str.lower()
    out["from_addr"] = out["payer_addr"].fillna(out["from"]).astype(str).str.lower()
    out["to_addr"] = out["recipient_addr"].fillna(out["to"]).astype(str).str.lower()
    out["value_usd"] = out["amount_usdc"].fillna(pd.to_numeric(out["value"], errors="coerce").fillna(0) / 1e18 * 2500)
    out["block_time"] = pd.to_datetime(pd.to_numeric(out["timeStamp"], errors="coerce"), unit="s", utc=True)
    min_ts = pd.to_numeric(out["timeStamp"], errors="coerce").min()
    out["block_time_s"] = pd.to_numeric(out["timeStamp"], errors="coerce") - min_ts
    out["block_number"] = pd.to_numeric(out["blockNumber"], errors="coerce").fillna(0).astype("int64")
    out["tx_hash"] = out["hash"]
    out["gas_used"] = pd.to_numeric(out["gasUsed"], errors="coerce").fillna(0).astype(float)
    out["gas_price_gwei"] = pd.to_numeric(out["gasPrice"], errors="coerce").fillna(0).astype(float) / 1e9
    out["method_id"] = out["methodId"].fillna("").astype(str).str.lower()
    out["success"] = out.get("txreceipt_status", "1").astype(str).eq("1")
    out["network"] = BASE_CHAIN_ID
    cols = [
        "network", "block_number", "block_time", "block_time_s", "tx_hash",
        "from_addr", "to_addr", "value_usd", "gas_used", "gas_price_gwei",
        "method_id", "success", "facilitator_addr", "watched_address",
        "is_x402_eip3009", "decoded_method", "amount_usdc", "valid_after",
        "valid_before", "authorization_nonce",
    ]
    return out[cols].sort_values("block_time").reset_index(drop=True)


def collect(out_dir: str = "data", tx_offset: int = 200) -> dict[str, Path]:
    root = Path(out_dir)
    raw_dir = root / "raw"
    processed_dir = root / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    facilitators = scrape_x402_watch_facilitators()
    coinbase_addresses = scrape_coinbase_addresses()
    support, supported_addresses = probe_supported(facilitators)
    all_addresses = pd.concat([coinbase_addresses, supported_addresses], ignore_index=True)
    if len(all_addresses) > 0:
        all_addresses = all_addresses.drop_duplicates(subset=["network", "address", "address_role"])

    # Fetch txs for Base EVM addresses only. The OpenX402 signer gives active EIP-3009 x402 rows.
    evm_addresses = sorted(set(
        a.lower()
        for a in all_addresses.get("address", pd.Series(dtype=str)).dropna().astype(str)
        if a.startswith("0x")
    ))
    raw_txs = []
    for address in evm_addresses:
        raw_txs.append(fetch_blockscout_txlist(address, offset=tx_offset))
        time.sleep(0.2)
    raw_tx_df = pd.concat(raw_txs, ignore_index=True) if raw_txs else pd.DataFrame()
    real_x402 = normalise_x402_txs(raw_tx_df)

    paths = {
        "facilitators": raw_dir / "x402_facilitators.parquet",
        "support": raw_dir / "x402_supported_probe.parquet",
        "addresses": raw_dir / "x402_addresses.parquet",
        "raw_txs": raw_dir / "base_facilitator_txlist.parquet",
        "real_x402": processed_dir / "real_x402_base.parquet",
        "sample_facilitators": raw_dir / "sample_x402_facilitators.csv",
        "sample_addresses": raw_dir / "sample_x402_addresses.csv",
        "sample_real_x402": processed_dir / "sample_real_x402_base.csv",
    }
    facilitators.to_parquet(paths["facilitators"], index=False)
    support.to_parquet(paths["support"], index=False)
    all_addresses.to_parquet(paths["addresses"], index=False)
    raw_tx_df.to_parquet(paths["raw_txs"], index=False)
    real_x402.to_parquet(paths["real_x402"], index=False)

    facilitators.head(50).to_csv(paths["sample_facilitators"], index=False)
    all_addresses.head(100).to_csv(paths["sample_addresses"], index=False)
    real_x402[real_x402["is_x402_eip3009"]].head(100).to_csv(paths["sample_real_x402"], index=False)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out_dir", type=str, default="data")
    parser.add_argument("--tx_offset", type=int, default=200)
    args = parser.parse_args()
    paths = collect(out_dir=args.out_dir, tx_offset=args.tx_offset)
    print("collected public x402 data:")
    for name, path in paths.items():
        print(f"  {name:20} {path}")
    real = pd.read_parquet(paths["real_x402"])
    if len(real):
        print()
        print(f"normalised txs: {len(real):,}")
        print(f"decoded x402 EIP-3009 rows: {int(real['is_x402_eip3009'].sum()):,}")
        print(f"unique payers: {real.loc[real['is_x402_eip3009'], 'from_addr'].nunique():,}")
        print(f"unique recipients: {real.loc[real['is_x402_eip3009'], 'to_addr'].nunique():,}")


if __name__ == "__main__":
    main()
