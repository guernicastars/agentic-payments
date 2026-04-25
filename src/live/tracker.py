"""Live fraud tracker for the pitch demo.

Usage in Streamlit (e.g. inside an `@st.fragment(run_every="1s")`):

    from src.live.tracker import LiveTracker, ReplayStream

    if "tracker" not in st.session_state:
        st.session_state.tracker = LiveTracker(ReplayStream("data/processed/real_x402_payments.parquet"))
    event = st.session_state.tracker.tick()
    if event is not None:
        ...

Architecture (per memo 13 + Plan-agent sanity check):
  * Score is a *population* statistic (`src/models/score.py:_baseline_zscore`).
    On every tick we recompute features and scores for the entire live
    population, not just the source wallet. With ~100s of wallets this is
    sub-100ms.
  * Alerts fire only on the wallet that received a new tx this tick
    (otherwise other wallets' scores jiggling as the population grows
    cause spurious alerts).
  * Alert criterion is *percentile-based* against the live population
    (top-5%), not the absolute composite-score thresholds in
    `_suspicion_tier`. Absolute thresholds drift as population shape
    changes; percentile is stable.
  * Warm-up gate: no alerts until the population has at least
    `MIN_POPULATION` wallets AND the source wallet has at least
    `MIN_WALLET_TX` transactions in its buffer.
  * Replay clock is *step-based* (one tx per `step_seconds`), not real
    block time -- otherwise inter-block gaps could give multi-second
    dead pauses mid-pitch.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd

from src.features.fingerprint import compute_features
from src.models.score import score_wallets


# Warm-up thresholds. Tuned against the 437-tx public x402 sample on Base
# (data/processed/real_x402_payments.parquet) where ~7 wallets reach 20+ tx.
# Curated replay grows population to ~30 within the first ~30 ticks so a
# 2-min demo at 1s/tick clears warm-up well before the headline beat.
MIN_POPULATION = 25
MIN_WALLET_TX = 8
ALERT_PERCENTILE = 0.92   # top ~8% of population
TX_BUFFER_PER_WALLET = 200


@dataclass
class TickEvent:
    """One step of the live stream."""
    tx: pd.Series                     # the new transaction row
    population_size: int              # unique payers seen so far
    warming_up: bool                  # warm-up gate active
    scores: pd.DataFrame              # full live-population score frame, sorted desc
    alert: dict | None = None         # non-None when this tx caused a new alert


class TxStream:
    """Abstract iterator of canonical-schema tx rows."""
    def __iter__(self) -> Iterator[dict]:
        raise NotImplementedError


class ReplayStream(TxStream):
    """Yield rows from a recorded parquet, one per call to next().

    Sorting: defaults to `block_time_s` ascending, but the caller can pass
    `presort_fn(df) -> df` to hand-curate the demo order (e.g.\\ to land a
    suspicious wallet at the 45s mark).
    """

    def __init__(
        self,
        parquet_path: str | Path,
        sort_by: str = "block_time_s",
        presort_fn=None,
    ) -> None:
        df = pd.read_parquet(parquet_path)
        if presort_fn is not None:
            df = presort_fn(df)
        elif sort_by in df.columns:
            df = df.sort_values(sort_by, kind="stable").reset_index(drop=True)
        self._df = df
        self._cursor = 0

    def __iter__(self) -> Iterator[dict]:
        return self

    def __next__(self) -> dict:
        if self._cursor >= len(self._df):
            raise StopIteration
        row = self._df.iloc[self._cursor]
        self._cursor += 1
        return row.to_dict()

    def __len__(self) -> int:
        return len(self._df)

    @property
    def remaining(self) -> int:
        return max(0, len(self._df) - self._cursor)


def demo_replay(parquet_path: str | Path) -> ReplayStream:
    """Hand-curated demo ordering.

    Strategy: a *round-robin* opening so the ticker visibly fills with
    distinct wallets and the population gate clears fast. After every wallet
    has been seen at least once we revert to natural block-time order so
    rapid bursts from prolific wallets keep their realistic arrival pattern.
    """

    def presort(df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_values("block_time_s", kind="stable").reset_index(drop=True)
        if len(df) == 0:
            return df
        # Phase 1 (~25 ticks): one tx from each of the top-25 wallets by
        # tx count. Population grows by 1 per tick, hitting MIN_POPULATION
        # fast. Prolific wallets are seeded first.
        # Phase 2: natural block-time order for everything else. The
        # already-seeded prolific wallets quickly cross MIN_WALLET_TX
        # because they dominate the natural-order tail.
        groups = {a: g.copy() for a, g in df.groupby("from_addr", sort=False)}
        wallet_order = df["from_addr"].value_counts().index.tolist()
        opening_idx: list[int] = [groups[a].index[0] for a in wallet_order[:25]]
        opening_df = df.loc[opening_idx]
        tail = df[~df.index.isin(opening_idx)].copy()
        return pd.concat([opening_df, tail], ignore_index=True)

    return ReplayStream(parquet_path, presort_fn=presort)


class LiveTracker:
    """Owns per-wallet tx buffers, scoring, and alert state."""

    def __init__(self, stream: TxStream) -> None:
        self._stream = iter(stream)
        self._buffers: dict[str, deque] = {}
        self._last_alert_at: dict[str, int] = {}  # wallet -> tick number when last alerted
        self._tick_no = 0
        self._alerts_history: list[dict] = []

    @property
    def stream(self) -> TxStream:
        return self._stream

    @property
    def population_size(self) -> int:
        return len(self._buffers)

    @property
    def alerts(self) -> list[dict]:
        return list(self._alerts_history)

    @property
    def total_tx_seen(self) -> int:
        return sum(len(b) for b in self._buffers.values())

    def reset(self, stream: TxStream | None = None) -> None:
        if stream is not None:
            self._stream = iter(stream)
        self._buffers.clear()
        self._last_alert_at.clear()
        self._tick_no = 0
        self._alerts_history.clear()

    def tick(self) -> TickEvent | None:
        """Pull one tx, update state, produce a TickEvent. None if stream is empty."""
        try:
            tx = next(self._stream)
        except StopIteration:
            return None
        self._tick_no += 1

        wallet = str(tx.get("from_addr", ""))
        if not wallet:
            return None

        buf = self._buffers.setdefault(wallet, deque(maxlen=TX_BUFFER_PER_WALLET))
        buf.append(tx)

        # Build a population-level tx frame and score the whole thing.
        # ~100s of wallets * 200 tx is sub-100ms; skip incremental tricks.
        flat: list[dict] = []
        for rows in self._buffers.values():
            flat.extend(rows)
        tx_frame = pd.DataFrame(flat)

        try:
            features = compute_features(tx_frame).fillna(0.0)
            scored = score_wallets(features) if len(features) else pd.DataFrame()
        except Exception:
            scored = pd.DataFrame()

        warming_up = (
            self.population_size < MIN_POPULATION
            or len(buf) < MIN_WALLET_TX
            or len(scored) == 0
        )

        alert = None
        if (
            not warming_up
            and wallet in scored.index
            and len(scored) >= MIN_POPULATION
        ):
            wallet_score = float(scored.loc[wallet, "composite_score"])
            cutoff = float(scored["composite_score"].quantile(ALERT_PERCENTILE))
            # Cooldown: don't re-alert the same wallet within 30 ticks
            # (~30s at 1s/tick) — keeps the alert panel from being a single
            # wallet's repeating receipt.
            cooled = (self._tick_no - self._last_alert_at.get(wallet, -10**6)) > 30
            if wallet_score >= cutoff and cooled:
                row = scored.loc[wallet]
                alert = {
                    "tick": self._tick_no,
                    "wallet": wallet,
                    "wallet_short": wallet[:10],
                    "composite_score": wallet_score,
                    "tier": str(row["tier"]),
                    "explanation": str(row.get("explanation", "")),
                    "value_usd": float(tx.get("value_usd") or 0.0),
                    "tx_hash": str(tx.get("tx_hash", "")),
                    "to_addr_short": str(tx.get("to_addr", ""))[:10],
                }
                self._last_alert_at[wallet] = self._tick_no
                self._alerts_history.append(alert)

        return TickEvent(
            tx=pd.Series(tx),
            population_size=self.population_size,
            warming_up=warming_up,
            scores=scored,
            alert=alert,
        )
