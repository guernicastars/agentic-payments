"""Streamlit demo dashboard for agentic payment risk."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.live.tracker import LiveTracker, demo_replay
from src.pipeline import run_pipeline
from src.pipeline_dune import run_dune_pipeline


DATA = Path("data")
LIVE_REPLAY_PATH = DATA / "processed" / "real_x402_payments.parquet"

SYNTHETIC_PATHS = {
    "txs": DATA / "synthetic" / "run1.parquet",
    "labels": DATA / "synthetic" / "run1_labels.parquet",
    "features": DATA / "processed" / "features.parquet",
    "scores": DATA / "processed" / "scores.parquet",
    "clusters": DATA / "processed" / "clusters.parquet",
    "edges": DATA / "processed" / "cluster_edges.parquet",
    "embedding": DATA / "processed" / "embedding.parquet",
}

REAL_PATHS = {
    "txs": DATA / "processed" / "real_x402_payments.parquet",
    "features": DATA / "processed" / "real_x402_features.parquet",
    "scores": DATA / "processed" / "real_x402_scores.parquet",
    "embedding": DATA / "processed" / "real_x402_embedding.parquet",
}

DUNE_PATHS = {
    "txs": DATA / "processed" / "dune_x402_events.parquet",
    "labels": DATA / "processed" / "dune_x402_labels.parquet",
    "features": DATA / "processed" / "dune_x402_features.parquet",
    "scores": DATA / "processed" / "dune_x402_scores.parquet",
    "embedding": DATA / "processed" / "dune_x402_embedding.parquet",
    "snapshot_summary": DATA / "processed" / "dune_x402_snapshot_summary.parquet",
}

TIER_ORDER = ["critical", "high", "medium", "low", "unknown"]
TIER_COLORS = {
    "critical": "#e5484d",
    "high": "#f97316",
    "medium": "#f2c94c",
    "low": "#2dd4bf",
    "unknown": "#8892a0",
}
POLICY_COLORS = {
    "human_random": "#2dd4bf",
    "agent_arb_deterministic": "#60a5fa",
    "agent_payment_bot": "#a78bfa",
    "agent_compromised": "#f97316",
    "collusion_ring": "#e5484d",
    "dune_x402_payer": "#60a5fa",
    "base_baseline": "#2dd4bf",
    "unlabelled": "#8892a0",
}
FACTOR_LABELS = {
    "inter_arrival_anomaly": "Timing anomaly",
    "tod_uniformity_anomaly": "24h uniformity",
    "gas_tightness_anomaly": "Gas tightness",
    "counterparty_concentration": "Counterparty concentration",
    "method_concentration": "Method concentration",
    "burst_intensity": "Burst intensity",
    "drift_signal": "Late drift",
    "coordination": "Peer coordination",
}
FACTOR_COLUMNS = list(FACTOR_LABELS)


st.set_page_config(
    page_title="Agentic Payment Risk",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: #0b0d12;
            color: #e8edf2;
        }
        [data-testid="stHeader"] {
            background: rgba(11, 13, 18, 0.92);
        }
        .block-container {
            padding-top: 1.0rem;
            padding-bottom: 1.4rem;
            max-width: 1500px;
        }
        h1, h2, h3 {
            color: #f5f7fa;
            letter-spacing: 0;
        }
        h1 {
            font-size: 1.85rem;
            line-height: 1.15;
            margin-bottom: 0.15rem;
        }
        h2 {
            font-size: 1.1rem;
            margin-top: 0.2rem;
        }
        h3 {
            font-size: 0.98rem;
        }
        p, li, label, span {
            color: #b7c0ca;
        }
        [data-testid="stCaptionContainer"] {
            color: #8792a0;
        }
        div[data-testid="metric-container"] {
            background: #11151c;
            border: 1px solid #202733;
            border-radius: 8px;
            padding: 0.75rem 0.85rem;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.22);
        }
        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
            color: #f5f7fa;
            font-size: 1.45rem;
        }
        div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
            color: #94a3b8;
        }
        .section-card {
            background: #11151c;
            border: 1px solid #202733;
            border-radius: 8px;
            padding: 0.9rem 1rem;
        }
        .readout {
            background: #101820;
            border-left: 3px solid #2dd4bf;
            border-radius: 6px;
            padding: 0.75rem 0.9rem;
            color: #d7dee7;
            min-height: 116px;
        }
        .readout strong {
            color: #f5f7fa;
        }
        .badge {
            display: inline-block;
            border-radius: 999px;
            padding: 0.12rem 0.45rem;
            font-size: 0.72rem;
            font-weight: 650;
            border: 1px solid #2a3340;
            color: #dce3ea;
            background: #18202a;
            white-space: nowrap;
        }
        .badge-critical { color: #ffd6d6; background: rgba(229,72,77,0.18); border-color: rgba(229,72,77,0.35); }
        .badge-high { color: #fed7aa; background: rgba(249,115,22,0.16); border-color: rgba(249,115,22,0.36); }
        .badge-medium { color: #fff0b3; background: rgba(242,201,76,0.14); border-color: rgba(242,201,76,0.34); }
        .badge-low { color: #bffaf2; background: rgba(45,212,191,0.14); border-color: rgba(45,212,191,0.34); }
        .mono {
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            color: #dbe5ef;
        }
        .small-muted {
            color: #8792a0;
            font-size: 0.82rem;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid #202733;
            border-radius: 8px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.35rem;
        }
        .stTabs [data-baseweb="tab"] {
            background: #11151c;
            border: 1px solid #202733;
            border-radius: 8px;
            color: #b7c0ca;
            height: 2.25rem;
            padding: 0 0.9rem;
        }
        .stTabs [aria-selected="true"] {
            color: #ffffff;
            border-color: #3a4657;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_synthetic() -> dict[str, pd.DataFrame]:
    if not SYNTHETIC_PATHS["embedding"].exists() or not SYNTHETIC_PATHS["scores"].exists():
        run_pipeline()
    return {
        name: pd.read_parquet(path) if path.exists() else pd.DataFrame()
        for name, path in SYNTHETIC_PATHS.items()
    }


@st.cache_data(show_spinner=False)
def load_real() -> dict[str, pd.DataFrame]:
    return {
        name: pd.read_parquet(path) if path.exists() else pd.DataFrame()
        for name, path in REAL_PATHS.items()
    }


@st.cache_data(show_spinner=False)
def load_dune() -> dict[str, pd.DataFrame]:
    if not DUNE_PATHS["embedding"].exists() or not DUNE_PATHS["scores"].exists():
        run_dune_pipeline()
    return {
        name: pd.read_parquet(path) if path.exists() else pd.DataFrame()
        for name, path in DUNE_PATHS.items()
    }


def short_addr(addr: str, n: int = 6) -> str:
    if not isinstance(addr, str) or len(addr) < 12:
        return str(addr)
    return f"{addr[:n]}...{addr[-4:]}"


def tier_badge(tier: str) -> str:
    return f'<span class="badge badge-{tier}">{tier}</span>'


def dataset_frame(dataset: str) -> dict[str, pd.DataFrame]:
    if dataset == "Synthetic stress test":
        data = load_synthetic()
        labels = data["labels"].copy()
        if len(labels):
            labels = labels.set_index("addr")
        data["scored"] = data["scores"].join(labels, how="left") if len(labels) else data["scores"]
        data["dataset_kind"] = pd.DataFrame([{"kind": "synthetic"}])
        return data
    if dataset == "Dune x402 + baseline":
        data = load_dune()
        labels = data["labels"].copy()
        if len(labels):
            labels = labels.set_index("addr")
        data["scored"] = data["scores"].join(labels[["policy", "role", "ring_id"]], how="left") if len(labels) else data["scores"]
        data["clusters"] = pd.DataFrame()
        data["edges"] = pd.DataFrame()
        data["dataset_kind"] = pd.DataFrame([{"kind": "dune"}])
        return data
    data = load_real()
    scores = data["scores"].copy()
    scores["policy"] = "public_x402"
    scores["role"] = "observed"
    data["labels"] = pd.DataFrame()
    data["clusters"] = pd.DataFrame()
    data["edges"] = pd.DataFrame()
    data["scored"] = scores
    data["dataset_kind"] = pd.DataFrame([{"kind": "real"}])
    return data


def risk_level_counts(scores: pd.DataFrame) -> dict[str, int]:
    if len(scores) == 0:
        return {tier: 0 for tier in TIER_ORDER}
    return scores["tier"].value_counts().reindex(TIER_ORDER).fillna(0).astype(int).to_dict()


def selected_default(scored: pd.DataFrame) -> str | None:
    if len(scored) == 0:
        return None
    for tier in ["critical", "high", "medium", "low"]:
        sub = scored[scored["tier"] == tier]
        if len(sub):
            return str(sub.index[0])
    return str(scored.index[0])


def build_alert_queue(scored: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    if len(scored) == 0:
        return pd.DataFrame()
    rows = scored.join(features[["tx_count", "counterparty_top1_share", "method_top1_share"]], how="left")
    out = rows.reset_index().rename(columns={"from_addr": "wallet", "index": "wallet"})
    out["wallet_short"] = out["wallet"].apply(short_addr)
    out["score"] = out["composite_score"].round(1)
    out["tx_count"] = out["tx_count"].fillna(0).astype(int)
    out["counterparty_top1_share"] = (out["counterparty_top1_share"].fillna(0) * 100).round(0).astype(int)
    out["method_top1_share"] = (out["method_top1_share"].fillna(0) * 100).round(0).astype(int)
    out["policy"] = out.get("policy", "unlabelled").fillna("unlabelled")
    out["reason"] = out["explanation"].fillna("").str.slice(0, 120)
    out["action"] = out["tier"].map({
        "critical": "Freeze + review",
        "high": "Step-up auth",
        "medium": "Monitor",
        "low": "Allow",
    }).fillna("Review")
    return out[
        [
            "wallet",
            "wallet_short",
            "score",
            "tier",
            "action",
            "policy",
            "tx_count",
            "counterparty_top1_share",
            "method_top1_share",
            "reason",
        ]
    ]


def score_bar(value: float, width: int = 140) -> str:
    value = max(0.0, min(100.0, float(value)))
    color = TIER_COLORS["low"]
    if value >= 75:
        color = TIER_COLORS["critical"]
    elif value >= 50:
        color = TIER_COLORS["high"]
    elif value >= 25:
        color = TIER_COLORS["medium"]
    return (
        f'<div style="width:{width}px;height:8px;background:#202733;border-radius:999px;overflow:hidden;">'
        f'<div style="width:{value:.0f}%;height:8px;background:{color};border-radius:999px;"></div>'
        "</div>"
    )


def metric_row(data: dict[str, pd.DataFrame], dataset: str) -> None:
    txs = data["txs"]
    scores = data["scores"]
    scored = data["scored"]
    high = scored[scored["tier"].isin(["critical", "high"])] if len(scored) else pd.DataFrame()
    medium = scored[scored["tier"] == "medium"] if len(scored) else pd.DataFrame()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Transactions", f"{len(txs):,}")
    c2.metric("Wallets scored", f"{len(scores):,}")
    c3.metric("Immediate queue", f"{len(high):,}")
    c4.metric("Watchlist", f"{len(medium):,}")
    if dataset == "Synthetic stress test" and "policy" in scored:
        compromised = scored[scored["policy"] == "agent_compromised"]
        recall = compromised["tier"].isin(["critical", "high"]).mean() * 100 if len(compromised) else 0
        c5.metric("Compromise recall", f"{recall:.0f}%")
    else:
        recipients = txs["to_addr"].nunique() if "to_addr" in txs else 0
        c5.metric("Recipients", f"{recipients:,}")


def readout(data: dict[str, pd.DataFrame], dataset: str) -> None:
    counts = risk_level_counts(data["scores"])
    txs = data["txs"]
    scored = data["scored"]
    if dataset == "Synthetic stress test":
        human_high = 0
        if "policy" in scored and len(scored):
            flagged = scored[scored["tier"].isin(["critical", "high"])]
            human_high = len(flagged[flagged["policy"] == "human_random"])
        text = (
            f"<strong>Synthetic validation.</strong><br>"
            f"{counts['high'] + counts['critical']} wallets are in the immediate queue, "
            f"{counts['medium']} require monitoring, and {human_high} human wallets are false-high. "
            "The demo proves the pipeline can separate deterministic agents, compromised drift, and collusion rings with known ground truth."
        )
    elif dataset == "Dune x402 + baseline":
        is_x402 = int(data["txs"].get("is_x402", pd.Series(dtype=bool)).sum()) if len(data["txs"]) else 0
        baseline = len(data["txs"]) - is_x402
        summary = data.get("snapshot_summary", pd.DataFrame())
        current = summary[summary["snapshot"] == "current"].iloc[0].to_dict() if len(summary) and "snapshot" in summary else {}
        current_rows = int(current.get("rows", 0) or 0)
        current_payers = int(current.get("payers", 0) or 0)
        text = (
            f"<strong>CTO Dune pull.</strong><br>"
            f"{is_x402:,} x402 settlement rows cooked against {baseline:,} ordinary Base baseline rows. "
            f"The Dune snapshot table shows {current_rows:,} current-window rows from {current_payers:,} payers; "
            f"this gives us the first clean trend + baseline view without relying on synthetic-only evidence."
        )
    else:
        first = txs["block_time"].min() if "block_time" in txs and len(txs) else None
        last = txs["block_time"].max() if "block_time" in txs and len(txs) else None
        window = f"{first:%b %d} to {last:%b %d}" if first is not None and last is not None else "current pull"
        text = (
            f"<strong>Public x402 overlay.</strong><br>"
            f"{len(txs):,} decoded Base USDC x402 payments across {window}. "
            f"The current pull produces {counts['medium']} medium-risk wallets and no high-severity policy breaches, "
            "which is the honest read until labels or larger history arrive."
        )
    st.markdown(f'<div class="readout">{text}</div>', unsafe_allow_html=True)


def embedding_chart(embedding: pd.DataFrame, color_by: str) -> go.Figure:
    if len(embedding) == 0:
        return go.Figure()
    color_map = TIER_COLORS if color_by == "tier" else POLICY_COLORS
    fig = px.scatter(
        embedding,
        x="x",
        y="y",
        color=color_by,
        color_discrete_map=color_map,
        category_orders={"tier": TIER_ORDER},
        size="tx_count",
        size_max=16,
        hover_name="from_addr",
        hover_data={
            "policy": True if "policy" in embedding else False,
            "tier": True,
            "composite_score": ":.1f",
            "tx_count": ":.0f",
            "x": False,
            "y": False,
        },
    )
    fig.update_traces(marker=dict(line=dict(width=0.4, color="#0b0d12"), opacity=0.9))
    fig.update_layout(
        height=460,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#11151c",
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color="#b7c0ca")),
    )
    return fig


def tier_mix(scores: pd.DataFrame) -> go.Figure:
    counts = scores["tier"].value_counts().reindex(TIER_ORDER).fillna(0).reset_index()
    counts.columns = ["tier", "wallets"]
    counts = counts[counts["wallets"] > 0]
    fig = px.bar(
        counts,
        x="tier",
        y="wallets",
        color="tier",
        color_discrete_map=TIER_COLORS,
        category_orders={"tier": TIER_ORDER},
        text="wallets",
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(
        height=240,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#11151c",
        showlegend=False,
        xaxis=dict(title=None, tickfont=dict(color="#9aa6b2"), showgrid=False),
        yaxis=dict(title=None, tickfont=dict(color="#9aa6b2"), gridcolor="#202733"),
    )
    return fig


def factor_chart(scores: pd.DataFrame, wallet: str) -> go.Figure:
    if wallet not in scores.index:
        return go.Figure()
    row = scores.loc[wallet, FACTOR_COLUMNS].rename(FACTOR_LABELS).sort_values()
    frame = row.reset_index()
    frame.columns = ["factor", "score"]
    fig = px.bar(
        frame,
        x="score",
        y="factor",
        orientation="h",
        color="score",
        color_continuous_scale=["#2dd4bf", "#f2c94c", "#f97316", "#e5484d"],
        range_color=[0, 100],
        text=frame["score"].round(0),
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(
        height=310,
        margin=dict(l=0, r=20, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#11151c",
        coloraxis_showscale=False,
        xaxis=dict(range=[0, 105], title=None, tickfont=dict(color="#9aa6b2"), gridcolor="#202733"),
        yaxis=dict(title=None, tickfont=dict(color="#b7c0ca")),
    )
    return fig


def network_chart(edges: pd.DataFrame, scores: pd.DataFrame) -> go.Figure:
    if len(edges) == 0:
        fig = go.Figure()
        fig.update_layout(
            height=360,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#11151c",
            annotations=[dict(text="No coordination edges in this dataset", showarrow=False, font=dict(color="#8792a0"))],
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig
    top_edges = edges.sort_values("similarity", ascending=False).head(260)
    graph = nx.Graph()
    for _, row in top_edges.iterrows():
        graph.add_edge(row["w1"], row["w2"], weight=float(row["similarity"]))
    pos = nx.spring_layout(graph, seed=42, k=0.32)
    edge_x, edge_y = [], []
    for u, v in graph.edges():
        edge_x.extend([pos[u][0], pos[v][0], None])
        edge_y.extend([pos[u][1], pos[v][1], None])
    nodes = []
    for node in graph.nodes():
        score = float(scores.loc[node, "composite_score"]) if node in scores.index else 0.0
        tier = scores.loc[node, "tier"] if node in scores.index else "unknown"
        nodes.append({"wallet": node, "x": pos[node][0], "y": pos[node][1], "score": score, "tier": tier})
    node_df = pd.DataFrame(nodes)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(color="rgba(136,146,160,0.23)", width=1),
        hoverinfo="skip",
        showlegend=False,
    ))
    for tier in TIER_ORDER:
        sub = node_df[node_df["tier"] == tier]
        if len(sub) == 0:
            continue
        fig.add_trace(go.Scatter(
            x=sub["x"],
            y=sub["y"],
            mode="markers",
            name=tier,
            marker=dict(
                color=TIER_COLORS[tier],
                size=(sub["score"] / 4.8).clip(lower=7, upper=18),
                line=dict(color="#0b0d12", width=0.7),
            ),
            text=sub["wallet"].map(short_addr),
            hovertemplate="%{text}<br>%{fullData.name}<extra></extra>",
        ))
    fig.update_layout(
        height=360,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#11151c",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color="#b7c0ca")),
    )
    return fig


def case_summary(scored: pd.DataFrame, features: pd.DataFrame, wallet: str) -> None:
    if wallet not in scored.index:
        return
    row = scored.loc[wallet]
    feat = features.loc[wallet] if wallet in features.index else pd.Series(dtype=float)
    left, right = st.columns([0.9, 1.2], gap="large")
    with left:
        st.markdown(
            f"""
            <div class="section-card">
              <div class="small-muted">Selected wallet</div>
              <div class="mono" style="font-size:0.95rem;margin:0.25rem 0 0.5rem;">{wallet}</div>
              {tier_badge(str(row["tier"]))}
              <div style="height:0.65rem;"></div>
              <div class="small-muted">Composite score</div>
              <div style="display:flex;align-items:center;gap:0.7rem;margin-top:0.25rem;">
                {score_bar(float(row["composite_score"]), width=180)}
                <strong style="color:#f5f7fa;">{float(row["composite_score"]):.1f}</strong>
              </div>
              <div style="height:0.75rem;"></div>
              <div class="small-muted">Recommended action</div>
              <strong style="color:#f5f7fa;">{ {"critical": "Freeze + review", "high": "Step-up auth", "medium": "Monitor", "low": "Allow"}.get(str(row["tier"]), "Review") }</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        tx_count = int(feat.get("tx_count", 0))
        cp = feat.get("counterparty_top1_share", 0.0) * 100
        method = feat.get("method_top1_share", 0.0) * 100
        cv = feat.get("inter_arrival_cv", 0.0)
        st.markdown(
            f"""
            <div class="section-card">
              <div class="small-muted">Why it was flagged</div>
              <div style="color:#dce3ea;margin-top:0.3rem;">{row.get("explanation", "")}</div>
              <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.7rem;margin-top:0.9rem;">
                <div><div class="small-muted">Tx count</div><strong style="color:#f5f7fa;">{tx_count:,}</strong></div>
                <div><div class="small-muted">Top counterparty</div><strong style="color:#f5f7fa;">{cp:.0f}%</strong></div>
                <div><div class="small-muted">Top method</div><strong style="color:#f5f7fa;">{method:.0f}%</strong></div>
                <div><div class="small-muted">Timing CV</div><strong style="color:#f5f7fa;">{cv:.2f}</strong></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_alert_queue(data: dict[str, pd.DataFrame]) -> str | None:
    queue = build_alert_queue(data["scored"], data["features"])
    if len(queue) == 0:
        st.info("No wallets to score.")
        return None
    selected = selected_default(data["scored"])
    display = queue.head(18).copy()
    display["risk"] = display["tier"].map(lambda t: t.upper())
    st.dataframe(
        display[
            [
                "wallet_short",
                "score",
                "risk",
                "action",
                "policy",
                "tx_count",
                "counterparty_top1_share",
                "method_top1_share",
                "reason",
            ]
        ],
        width="stretch",
        hide_index=True,
        height=410,
        column_config={
            "wallet_short": "Wallet",
            "score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.1f"),
            "risk": "Tier",
            "tx_count": "Tx",
            "counterparty_top1_share": st.column_config.NumberColumn("Top CP %", format="%d%%"),
            "method_top1_share": st.column_config.NumberColumn("Top Method %", format="%d%%"),
            "reason": "Evidence",
        },
    )
    return selected


def _live_tracker_state(reset: bool = False) -> LiveTracker:
    if reset or "live_tracker" not in st.session_state:
        st.session_state.live_tracker = LiveTracker(demo_replay(LIVE_REPLAY_PATH))
        st.session_state.live_ticker = []  # last N tx for the ticker view
        st.session_state.live_paused = False
    return st.session_state.live_tracker


@st.fragment(run_every="1s")
def _live_fragment() -> None:
    """Refreshes once per second; the rest of the dashboard does NOT rerun."""
    tracker: LiveTracker = st.session_state.live_tracker

    if not st.session_state.get("live_paused", False):
        event = tracker.tick()
        if event is not None:
            ticker = st.session_state.live_ticker
            ticker.append({
                "time": pd.Timestamp.now().strftime("%H:%M:%S"),
                "wallet": str(event.tx.get("from_addr", ""))[:10] + "...",
                "to": str(event.tx.get("to_addr", ""))[:10] + "...",
                "value_usd": float(event.tx.get("value_usd") or 0.0),
                "alert": "ALERT" if event.alert else "",
            })
            st.session_state.live_ticker = ticker[-12:]
            st.session_state.live_population = event.population_size
            st.session_state.live_warming = event.warming_up
            st.session_state.live_remaining = getattr(tracker.stream, "remaining", -1)

    pop = st.session_state.get("live_population", 0)
    warming = st.session_state.get("live_warming", True)
    remaining = st.session_state.get("live_remaining", -1)
    n_tx_seen = tracker.total_tx_seen
    n_alerts = len(tracker.alerts)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TX seen", f"{n_tx_seen:,}")
    c2.metric("Wallets observed", f"{pop:,}")
    c3.metric("Alerts raised", f"{n_alerts:,}")
    if warming:
        from src.live.tracker import MIN_POPULATION
        c4.metric("Status", f"warming up ({pop}/{MIN_POPULATION})")
    elif remaining >= 0:
        c4.metric("Stream", f"{remaining} tx remaining")
    else:
        c4.metric("Status", "live")

    st.markdown("##### Last alerts")
    if not tracker.alerts:
        st.markdown(
            f'<div class="section-card" style="color:#94a3b8;">'
            f'no alerts yet '
            f'{"(warming up — need {MIN_POPULATION}+ wallets)" if warming else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        from src.models.score import SUBSCORE_LABEL
        for alert in tracker.alerts[-4:][::-1]:
            badge = tier_badge(alert["tier"])
            decision = (
                "BLOCK" if (alert["tier"] == "critical"
                            or alert.get("top_factor_value", 0) >= 90)
                else "REVIEW"
            )
            decision_color = "#e5484d" if decision == "BLOCK" else "#f97316"
            top_factor_label = SUBSCORE_LABEL.get(
                alert.get("top_factor_name", ""),
                alert.get("top_factor_name", "overall"),
            )
            top_factor_value = alert.get("top_factor_value", 0.0)
            # Sub-score badge row
            sub_pills = ""
            for k, v in (alert.get("subscores") or {}).items():
                lbl = SUBSCORE_LABEL.get(k, k)
                emphasised = (k == alert.get("top_factor_name"))
                color = "#2dd4bf" if emphasised else "#8792a0"
                sub_pills += (
                    f'<span style="display:inline-block;border:1px solid {color};'
                    f'color:{color};border-radius:999px;padding:0.05rem 0.5rem;'
                    f'margin:0 0.2rem 0.2rem 0;font-size:0.72rem;">'
                    f'{lbl} {v:.0f}</span>'
                )
            st.markdown(
                f'<div class="section-card" style="margin-bottom:0.45rem;'
                f'border-left:3px solid {decision_color};">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<div><span class="mono">{alert["wallet_short"]}...</span> '
                f'&nbsp;{badge}&nbsp;'
                f'<span class="small-muted">tick {alert["tick"]}</span>&nbsp;'
                f'<span style="color:{decision_color};font-weight:600;font-size:0.78rem;'
                f'border:1px solid {decision_color};border-radius:4px;padding:0.05rem 0.4rem;">'
                f'{decision}</span></div>'
                f'<div style="color:#f5f7fa;font-weight:600;">{alert.get("overall_action_risk", alert["composite_score"]):.1f}</div>'
                f'</div>'
                f'<div style="color:#f5f7fa;margin-top:0.35rem;font-size:0.85rem;">'
                f'<strong>{top_factor_label}:</strong> {top_factor_value:.0f}/100'
                f'</div>'
                f'<div style="margin-top:0.35rem;">{sub_pills}</div>'
                f'<div style="color:#b7c0ca;margin-top:0.4rem;font-size:0.86rem;">'
                f'{alert["explanation"]}'
                f'</div>'
                f'<div class="small-muted" style="margin-top:0.3rem;">'
                f'paid <span class="mono">{alert["to_addr_short"]}...</span>'
                f' &middot; ${alert["value_usd"]:.4f}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("##### Stream ticker")
    ticker = st.session_state.get("live_ticker", [])
    if not ticker:
        st.caption("waiting for next event...")
    else:
        st.dataframe(
            pd.DataFrame(ticker[::-1]),
            width="stretch",
            hide_index=True,
            height=320,
            column_config={
                "time": "Time",
                "wallet": "Payer",
                "to": "Merchant",
                "value_usd": st.column_config.NumberColumn("USD", format="$%.4f"),
                "alert": "Alert",
            },
        )


def render_live_tracker() -> None:
    st.subheader("Live action risk stream")
    st.caption(
        "Replay of recently-decoded Base x402 settlements. Each tick = one action; "
        "scores recomputed on the full live population. An alert fires when a "
        "wallet's overall action risk enters the top-8% percentile **or** any "
        "sub-score (agent-likeness · drift · coordination · policy violation · "
        "counterparty risk · prompt-injection) crosses 75/100. Each alert is "
        "labelled as Allow / Review / Block — runtime control, not just analytics."
    )
    _live_tracker_state()
    cols = st.columns([0.20, 0.20, 0.60])
    if cols[0].button("Restart", width="stretch"):
        _live_tracker_state(reset=True)
        st.session_state.live_ticker = []
        st.rerun()
    paused = st.session_state.get("live_paused", False)
    if cols[1].button("Resume" if paused else "Pause", width="stretch"):
        st.session_state.live_paused = not paused
        st.rerun()
    cols[2].caption("Replay ticks at 1 tx/second. Hand-curated order: prolific wallets seeded first to clear warm-up within ~30s.")
    _live_fragment()


def render_tabs(data: dict[str, pd.DataFrame], dataset: str) -> None:
    live, triage, behaviour, coordination, evidence, trend = st.tabs(
        ["Live Risk", "Triage", "Behaviour Map", "Coordination", "Model Evidence", "12-month Trend"]
    )
    with live:
        render_live_tracker()

    with triage:
        left, right = st.columns([1.45, 1.0], gap="large")
        with left:
            st.subheader("Alert Queue")
            selected = render_alert_queue(data)
        with right:
            st.subheader("Selected Case")
            wallet = st.selectbox(
                "Wallet",
                data["scored"].index.tolist(),
                index=data["scored"].index.tolist().index(selected) if selected in data["scored"].index else 0,
                format_func=lambda w: f"{short_addr(w)}  {data['scores'].loc[w, 'composite_score']:.1f}  {data['scores'].loc[w, 'tier']}",
                label_visibility="collapsed",
            )
            case_summary(data["scored"], data["features"], wallet)
            st.plotly_chart(factor_chart(data["scores"], wallet), width="stretch")

    with behaviour:
        top, bottom = st.columns([1.55, 0.9], gap="large")
        with top:
            st.subheader("Behavioural Fingerprint Space")
            options = ["tier"]
            if "policy" in data["embedding"].columns and data["embedding"]["policy"].nunique() > 1:
                options.append("policy")
            color_by = st.segmented_control("Colour", options, default="tier", label_visibility="collapsed")
            st.plotly_chart(embedding_chart(data["embedding"], color_by), width="stretch")
        with bottom:
            st.subheader("Risk Tiers")
            st.plotly_chart(tier_mix(data["scores"]), width="stretch")
            st.markdown(
                '<div class="small-muted">Each point is a wallet. Distance means similar timing, gas, counterparty, value, method, and coordination fingerprints.</div>',
                unsafe_allow_html=True,
            )

    with coordination:
        left, right = st.columns([1.4, 1.0], gap="large")
        with left:
            st.subheader("Wallet Coordination Graph")
            st.plotly_chart(network_chart(data["edges"], data["scores"]), width="stretch")
        with right:
            st.subheader("Detected Clusters")
            clusters = data["clusters"]
            if len(clusters):
                cluster_summary = (
                    clusters.groupby("cluster_id")
                    .agg(
                        wallets=("from_addr", "count"),
                        similarity=("similarity_score", "mean"),
                        timing=("timing_corr", "mean"),
                        counterparty=("counterparty_overlap", "mean"),
                        method=("method_agreement", "mean"),
                    )
                    .sort_values("similarity", ascending=False)
                    .reset_index()
                )
                cluster_summary["cluster"] = cluster_summary["cluster_id"].str.slice(0, 8)
                for col in ["similarity", "timing", "counterparty", "method"]:
                    cluster_summary[col] = (cluster_summary[col] * 100).round(0).astype(int)
                st.dataframe(
                    cluster_summary[["cluster", "wallets", "similarity", "timing", "counterparty", "method"]].head(12),
                    width="stretch",
                    hide_index=True,
                    height=360,
                    column_config={
                        "similarity": st.column_config.ProgressColumn("Similarity", min_value=0, max_value=100, format="%d%%"),
                        "timing": st.column_config.NumberColumn("Timing", format="%d%%"),
                        "counterparty": st.column_config.NumberColumn("Counterparty", format="%d%%"),
                        "method": st.column_config.NumberColumn("Method", format="%d%%"),
                    },
                )
            else:
                st.markdown('<div class="section-card">No cluster table for this dataset yet.</div>', unsafe_allow_html=True)

    with evidence:
        st.subheader("Risk Factor Distribution")
        factors = data["scores"][FACTOR_COLUMNS].rename(columns=FACTOR_LABELS)
        melted = factors.reset_index(drop=True).melt(var_name="factor", value_name="score")
        fig = px.box(
            melted,
            x="score",
            y="factor",
            color="factor",
            points=False,
            color_discrete_sequence=["#2dd4bf", "#60a5fa", "#a78bfa", "#f2c94c", "#f97316", "#e5484d", "#94a3b8", "#c084fc"],
        )
        fig.update_layout(
            height=420,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#11151c",
            showlegend=False,
            xaxis=dict(title="Factor score", range=[0, 100], gridcolor="#202733", tickfont=dict(color="#9aa6b2")),
            yaxis=dict(title=None, tickfont=dict(color="#b7c0ca")),
        )
        st.plotly_chart(fig, width="stretch")

    with trend:
        from src.viz.trend import load_or_locked, trend_figure_plotly

        agg, is_live = load_or_locked()
        st.subheader("Agent payment behaviour: Jun 2025 → Apr 2026")
        if is_live:
            st.caption("Live aggregation from `data/raw/x402_snapshot_*.parquet` (cofounder's Dune pull).")
        else:
            st.caption(
                "Locked numbers from memo 16 (`memos/16_snapshot_findings.md`). "
                "Falls back to live snapshots once `data/raw/x402_snapshot_*.parquet` files exist."
            )
        st.plotly_chart(trend_figure_plotly(agg), width="stretch")
        st.dataframe(
            agg[["date_label", "tx_count", "unique_payers", "unique_merchants", "median_tx_usd", "mean_tx_usd"]],
            width="stretch",
            hide_index=True,
            column_config={
                "date_label": "Snapshot",
                "tx_count": "Sample (tx)",
                "unique_payers": "Payers",
                "unique_merchants": "Merchants",
                "median_tx_usd": st.column_config.NumberColumn("Median tx", format="$%.3f"),
                "mean_tx_usd": st.column_config.NumberColumn("Mean tx", format="$%.2f"),
            },
        )
        st.markdown(
            '<div class="small-muted">Oct 2025 excluded — bipartite-degenerate sample '
            '(99.98% of volume routed through a single merchant). See memo 17.</div>',
            unsafe_allow_html=True,
        )


def main() -> None:
    inject_css()
    st.title("Agentic Payment Risk Console")
    st.caption("Wallet-level behavioural risk intelligence for AI-mediated payment traffic.")

    top_left, top_right = st.columns([0.72, 0.28], gap="large")
    with top_left:
        dataset = st.segmented_control(
            "Dataset",
            ["Synthetic stress test", "Dune x402 + baseline", "Public x402 Base"],
            default="Synthetic stress test",
        )
    data = dataset_frame(dataset)
    with top_right:
        st.markdown(
            f'<div style="text-align:right;margin-top:1.65rem;">{tier_badge("high") if dataset == "Synthetic stress test" else tier_badge("medium")} <span class="small-muted">current demo posture</span></div>',
            unsafe_allow_html=True,
        )

    readout(data, dataset)
    st.markdown("")
    metric_row(data, dataset)
    st.markdown("")
    render_tabs(data, dataset)


if __name__ == "__main__":
    main()
