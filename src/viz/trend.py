"""Snapshot trend aggregations and figures (D2 pitch artefact).

Reads the four per-snapshot parquets pulled by `scripts/pull_dune.py` and
produces:
  - per-snapshot summary table (unique payers, merchants, median/mean tx)
  - 4-panel matplotlib figure for `results/figures/trend.png` (slide)
  - plotly figure for the dashboard tab

Snapshot parquet schema (from pull_dune.py): block_time, payer, merchant,
value_usd. One file per snapshot at SNAPSHOT_PATHS below.

If no snapshot files are present, `LOCKED_NUMBERS` returns the 3-point
trend already locked in `memos/16_snapshot_findings.md` so the tab has
demo content from day one.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


SNAPSHOT_ORDER = ["early_adopters", "post_linux_fdn", "post_stripe", "current"]
SNAPSHOT_DATES = {
    "early_adopters": "Jun 2025",
    "post_linux_fdn": "Oct 2025",
    "post_stripe": "Jan 2026",
    "current": "Apr 2026",
}
SNAPSHOT_PATHS = {
    "early_adopters": Path("data/raw/x402_snapshot_2025_06_early_adopters.parquet"),
    "post_linux_fdn": Path("data/raw/x402_snapshot_2025_10_post_linux_fdn.parquet"),
    "post_stripe": Path("data/raw/x402_snapshot_2026_01_post_stripe.parquet"),
    "current": Path("data/raw/x402_snapshot_2026_04_current.parquet"),
}

# Excluded from the headline trend (bipartite-degenerate sample). See memo 14.
EXCLUDED_FROM_TREND = {"post_linux_fdn"}


# Locked numbers from memos/16_snapshot_findings.md. Used when none of the
# per-snapshot parquets are present (e.g. before scripts/pull_dune.py runs).
LOCKED_NUMBERS = pd.DataFrame(
    [
        {
            "snapshot": "early_adopters",
            "date_label": "Jun 2025",
            "tx_count": 151,
            "unique_payers": 39,
            "unique_merchants": 29,
            "median_tx_usd": 0.10,
            "mean_tx_usd": 124.0,
        },
        {
            "snapshot": "post_stripe",
            "date_label": "Jan 2026",
            "tx_count": 351,
            "unique_payers": 42,
            "unique_merchants": 53,
            "median_tx_usd": 0.01,
            "mean_tx_usd": 4.17,
        },
        {
            "snapshot": "current",
            "date_label": "Apr 2026",
            "tx_count": 400,
            "unique_payers": 55,
            "unique_merchants": 24,
            "median_tx_usd": 0.001,
            "mean_tx_usd": 1.63,
        },
    ]
)


def _summarise(label: str, sub: pd.DataFrame) -> dict:
    payer_col = "payer" if "payer" in sub.columns else "from_addr"
    merchant_col = "merchant" if "merchant" in sub.columns else "to_addr"
    return {
        "snapshot": label,
        "date_label": SNAPSHOT_DATES[label],
        "tx_count": len(sub),
        "unique_payers": int(sub[payer_col].nunique()),
        "unique_merchants": int(sub[merchant_col].nunique()),
        "median_tx_usd": float(sub["value_usd"].median()),
        "mean_tx_usd": float(sub["value_usd"].mean()),
        "volume_usd": float(sub["value_usd"].sum()),
    }


def aggregate_snapshots(snapshots_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate a single dataframe with a `snapshot` column. Used by tests."""
    rows = []
    for label in SNAPSHOT_ORDER:
        sub = snapshots_df[snapshots_df["snapshot"] == label]
        if len(sub) == 0:
            continue
        rows.append(_summarise(label, sub))
    return pd.DataFrame(rows)


def aggregate_from_files(
    paths: dict[str, Path] = SNAPSHOT_PATHS,
    include_excluded: bool = False,
) -> pd.DataFrame:
    """Read each per-snapshot parquet (cofounder's pull_dune.py output) and
    aggregate. Skips bipartite-degenerate snapshots unless include_excluded."""
    rows = []
    for label in SNAPSHOT_ORDER:
        if label in EXCLUDED_FROM_TREND and not include_excluded:
            continue
        p = paths.get(label)
        if p is None or not Path(p).exists():
            continue
        sub = pd.read_parquet(p)
        if len(sub) == 0:
            continue
        rows.append(_summarise(label, sub))
    return pd.DataFrame(rows)


def load_or_locked(
    paths: dict[str, Path] = SNAPSHOT_PATHS,
) -> tuple[pd.DataFrame, bool]:
    """Return (aggregate_df, is_live). is_live=False means the per-snapshot
    parquets were not found and we fell back to LOCKED_NUMBERS."""
    agg = aggregate_from_files(paths)
    if len(agg) == 0:
        return LOCKED_NUMBERS.copy(), False
    return agg, True


def trend_figure_plotly(agg: pd.DataFrame) -> go.Figure:
    """4-panel plotly figure matching the dashboard's dark theme."""
    panels = [
        ("unique_payers", "Unique agent wallets", False),
        ("median_tx_usd", "Median tx (USD)", True),
        ("unique_merchants", "Unique merchants", False),
        ("tx_count", "Sample size (tx)", False),
    ]
    fig = go.Figure().set_subplots(rows=2, cols=2, subplot_titles=[t for _, t, _ in panels])
    for i, (col, title, log_y) in enumerate(panels):
        r, c = (i // 2) + 1, (i % 2) + 1
        fig.add_trace(
            go.Scatter(
                x=agg["date_label"],
                y=agg[col],
                mode="lines+markers+text",
                line=dict(color="#2dd4bf", width=2.5),
                marker=dict(size=11, color="#2dd4bf", line=dict(color="#0b0d12", width=1.5)),
                text=[_fmt(v, log_y) for v in agg[col]],
                textposition="top center",
                textfont=dict(color="#dce3ea", size=10),
                showlegend=False,
                name=title,
            ),
            row=r,
            col=c,
        )
        if log_y:
            fig.update_yaxes(type="log", row=r, col=c)
    fig.update_layout(
        height=480,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#11151c",
        font=dict(color="#b7c0ca"),
    )
    fig.update_xaxes(gridcolor="#202733", tickfont=dict(color="#9aa6b2"))
    fig.update_yaxes(gridcolor="#202733", tickfont=dict(color="#9aa6b2"))
    for ann in fig.layout.annotations:
        ann.font.color = "#f5f7fa"
    return fig


def trend_figure_static(agg: pd.DataFrame, out_path: str | Path = "results/figures/trend.png") -> Path:
    """Matplotlib version for the slide deck (PNG)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    panels = [
        ("unique_payers", "Unique agent wallets", "{:,.0f}", False),
        ("median_tx_usd", "Median tx (USD)", "${:.3f}", True),
        ("unique_merchants", "Unique merchants", "{:,.0f}", False),
        ("tx_count", "Sample size (tx)", "{:,.0f}", False),
    ]
    for ax, (col, title, fmt, log_y) in zip(axes.flatten(), panels):
        ax.plot(agg["date_label"], agg[col], "o-", linewidth=2, markersize=9, color="#2a9d8f")
        ax.set_title(title)
        ax.grid(alpha=0.3)
        if log_y:
            ax.set_yscale("log")
        for x, y in zip(agg["date_label"], agg[col]):
            ax.annotate(fmt.format(y), (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    fig.suptitle("Agentic payment behaviour, Jun 2025 → Apr 2026", fontsize=13)
    fig.tight_layout()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def _fmt(v: float, log_y: bool) -> str:
    if log_y:
        if v >= 1:
            return f"${v:,.2f}"
        return f"${v:.3f}"
    return f"{v:,.0f}"


def main() -> None:
    """CLI entry: write results/figures/trend.png from snapshots (or locked numbers)."""
    agg, is_live = load_or_locked()
    out = trend_figure_static(agg)
    print(f"wrote {out} ({'live snapshots' if is_live else 'locked numbers'})")
    print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
