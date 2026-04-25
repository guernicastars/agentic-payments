"""Streamlit demo dashboard for agentic payment risk."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.pipeline import run_pipeline


DATA = Path("data")
TX_PATH = DATA / "synthetic" / "run1.parquet"
LABEL_PATH = DATA / "synthetic" / "run1_labels.parquet"
FEATURE_PATH = DATA / "processed" / "features.parquet"
SCORE_PATH = DATA / "processed" / "scores.parquet"
CLUSTER_PATH = DATA / "processed" / "clusters.parquet"
EDGE_PATH = DATA / "processed" / "cluster_edges.parquet"
EMBED_PATH = DATA / "processed" / "embedding.parquet"

TIER_ORDER = ["critical", "high", "medium", "low", "unknown"]
TIER_COLORS = {
    "critical": "#8b1e3f",
    "high": "#d95f02",
    "medium": "#d9a441",
    "low": "#2a9d8f",
    "unknown": "#87919e",
}
POLICY_COLORS = {
    "human_random": "#2a9d8f",
    "agent_arb_deterministic": "#3a6ea5",
    "agent_payment_bot": "#6f4e7c",
    "agent_compromised": "#d95f02",
    "collusion_ring": "#8b1e3f",
    "unlabelled": "#87919e",
}


st.set_page_config(
    page_title="Agentic Payment Risk",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data(show_spinner=False)
def load_or_build() -> dict[str, pd.DataFrame]:
    if not EMBED_PATH.exists() or not SCORE_PATH.exists() or not FEATURE_PATH.exists():
        run_pipeline()
    return {
        "txs": pd.read_parquet(TX_PATH),
        "labels": pd.read_parquet(LABEL_PATH),
        "features": pd.read_parquet(FEATURE_PATH),
        "scores": pd.read_parquet(SCORE_PATH),
        "clusters": pd.read_parquet(CLUSTER_PATH) if CLUSTER_PATH.exists() else pd.DataFrame(),
        "edges": pd.read_parquet(EDGE_PATH) if EDGE_PATH.exists() else pd.DataFrame(),
        "embedding": pd.read_parquet(EMBED_PATH),
    }


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: #f7f8f3;
            color: #17212b;
        }
        [data-testid="stHeader"] { background: rgba(247, 248, 243, 0.86); }
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 1rem;
            max-width: 1440px;
        }
        h1, h2, h3 { letter-spacing: 0; color: #17212b; }
        h1 { font-size: 2.0rem; margin-bottom: 0.1rem; }
        h3 { font-size: 1.0rem; }
        div[data-testid="metric-container"] {
            background: #ffffff;
            border: 1px solid #dfe4df;
            border-radius: 8px;
            padding: 0.65rem 0.8rem;
            box-shadow: 0 1px 2px rgba(23, 33, 43, 0.06);
        }
        .section {
            border-top: 1px solid #dfe4df;
            padding-top: 0.7rem;
            margin-top: 0.3rem;
        }
        .wallet-chip {
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            background: #17212b;
            color: #ffffff;
            border-radius: 6px;
            padding: 0.25rem 0.45rem;
            display: inline-block;
            margin-bottom: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def policy_label(name: str) -> str:
    return name.replace("agent_", "").replace("_", " ")


def metric_row(data: dict[str, pd.DataFrame]) -> None:
    txs = data["txs"]
    scores = data["scores"]
    labels = data["labels"].set_index("addr")
    scored = scores.join(labels, how="left")
    flagged = scored[scored["tier"].isin(["critical", "high"])]
    human_high = flagged[flagged["policy"] == "human_random"]
    compromised = scored[scored["policy"] == "agent_compromised"]
    compromised_hit = (compromised["tier"].isin(["critical", "high"]).mean() * 100) if len(compromised) else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Transactions", f"{len(txs):,}")
    c2.metric("Wallets", f"{scores.shape[0]:,}")
    c3.metric("High-Risk", f"{len(flagged):,}")
    c4.metric("Compromise Recall", f"{compromised_hit:.0f}%")
    c5.metric("Human False High", f"{len(human_high)}")


def embedding_chart(embedding: pd.DataFrame, color_by: str) -> go.Figure:
    color_map = TIER_COLORS if color_by == "tier" else POLICY_COLORS
    fig = px.scatter(
        embedding,
        x="x",
        y="y",
        color=color_by,
        color_discrete_map=color_map,
        category_orders={"tier": TIER_ORDER},
        size="tx_count",
        size_max=18,
        hover_name="from_addr",
        hover_data={
            "policy": True,
            "tier": True,
            "composite_score": ":.1f",
            "tx_count": ":.0f",
            "x": False,
            "y": False,
        },
    )
    fig.update_traces(marker=dict(line=dict(width=0.4, color="#ffffff"), opacity=0.82))
    fig.update_layout(
        height=510,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
    )
    return fig


def tier_mix(scores: pd.DataFrame) -> go.Figure:
    counts = scores["tier"].value_counts().reindex(TIER_ORDER).dropna().reset_index()
    counts.columns = ["tier", "wallets"]
    fig = px.bar(
        counts,
        x="tier",
        y="wallets",
        color="tier",
        color_discrete_map=TIER_COLORS,
        category_orders={"tier": TIER_ORDER},
    )
    fig.update_layout(
        height=245,
        margin=dict(l=0, r=0, t=4, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        showlegend=False,
        xaxis_title=None,
        yaxis_title=None,
    )
    return fig


def factor_chart(scores: pd.DataFrame, wallet: str) -> go.Figure:
    factors = [
        "inter_arrival_anomaly",
        "tod_uniformity_anomaly",
        "gas_tightness_anomaly",
        "counterparty_concentration",
        "method_concentration",
        "burst_intensity",
        "drift_signal",
        "coordination",
    ]
    row = scores.loc[wallet, factors].sort_values()
    fig = px.bar(
        row.reset_index(),
        x=wallet,
        y="index",
        orientation="h",
        color=wallet,
        color_continuous_scale=["#2a9d8f", "#d9a441", "#d95f02", "#8b1e3f"],
        range_color=[0, 100],
    )
    fig.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=4, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        coloraxis_showscale=False,
        xaxis_title=None,
        yaxis_title=None,
        xaxis=dict(range=[0, 100]),
    )
    return fig


def network_chart(edges: pd.DataFrame, scores: pd.DataFrame) -> go.Figure:
    if len(edges) == 0:
        return go.Figure()
    top_edges = edges.sort_values("similarity", ascending=False).head(220)
    G = nx.Graph()
    for _, row in top_edges.iterrows():
        G.add_edge(row["w1"], row["w2"], weight=float(row["similarity"]))
    pos = nx.spring_layout(G, seed=42, k=0.35)
    edge_x, edge_y = [], []
    for u, v in G.edges():
        edge_x.extend([pos[u][0], pos[v][0], None])
        edge_y.extend([pos[u][1], pos[v][1], None])
    node_rows = []
    for node in G.nodes():
        tier = scores.loc[node, "tier"] if node in scores.index else "unknown"
        score = float(scores.loc[node, "composite_score"]) if node in scores.index else 0.0
        node_rows.append({"wallet": node, "x": pos[node][0], "y": pos[node][1], "tier": tier, "score": score})
    nodes = pd.DataFrame(node_rows)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(color="rgba(23,33,43,0.18)", width=1),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    for tier in TIER_ORDER:
        sub = nodes[nodes["tier"] == tier]
        if len(sub) == 0:
            continue
        fig.add_trace(
            go.Scatter(
                x=sub["x"],
                y=sub["y"],
                mode="markers",
                name=tier,
                marker=dict(
                    color=TIER_COLORS[tier],
                    size=(sub["score"] / 5).clip(lower=7, upper=18),
                    line=dict(color="#ffffff", width=0.6),
                ),
                text=sub["wallet"],
                hovertemplate="%{text}<br>tier=%{fullData.name}<extra></extra>",
            )
        )
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=4, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0),
    )
    return fig


def main() -> None:
    inject_css()
    data = load_or_build()
    embedding = data["embedding"]
    scores = data["scores"]
    labels = data["labels"].set_index("addr")
    scored = scores.join(labels, how="left")

    st.title("Agentic Payment Risk")
    st.caption("Behavioural risk intelligence for agent traffic: fingerprint, cluster, score, explain.")
    metric_row(data)

    left, right = st.columns([1.65, 1.0], gap="large")
    with left:
        st.markdown('<div class="section"></div>', unsafe_allow_html=True)
        color_by = st.segmented_control("Colour", ["tier", "policy"], default="tier")
        st.plotly_chart(embedding_chart(embedding, color_by), width="stretch")

    with right:
        st.markdown('<div class="section"></div>', unsafe_allow_html=True)
        st.subheader("Risk Tiers")
        st.plotly_chart(tier_mix(scores), width="stretch")
        st.subheader("Highest-Risk Wallets")
        top = scored.reset_index().rename(columns={"from_addr": "wallet", "index": "wallet"}).head(9)
        top["wallet"] = top["wallet"].str.slice(0, 10)
        top["score"] = top["composite_score"].round(1)
        st.dataframe(
            top[["wallet", "score", "tier", "policy"]],
            width="stretch",
            hide_index=True,
            height=300,
        )

    bottom_left, bottom_right = st.columns([1.0, 1.0], gap="large")
    with bottom_left:
        st.markdown('<div class="section"></div>', unsafe_allow_html=True)
        ordered_wallets = scored.index.tolist()
        wallet = st.selectbox(
            "Wallet",
            ordered_wallets,
            index=0,
            format_func=lambda w: f"{w[:10]}...  {scores.loc[w, 'composite_score']:.1f}  {scores.loc[w, 'tier']}",
        )
        st.markdown(f'<span class="wallet-chip">{wallet}</span>', unsafe_allow_html=True)
        st.write(scores.loc[wallet, "explanation"])
        st.plotly_chart(factor_chart(scores, wallet), width="stretch")

    with bottom_right:
        st.markdown('<div class="section"></div>', unsafe_allow_html=True)
        st.subheader("Coordination Graph")
        st.plotly_chart(network_chart(data["edges"], scores), width="stretch")
        cluster_count = data["clusters"]["cluster_id"].nunique() if len(data["clusters"]) else 0
        covered = data["clusters"]["from_addr"].nunique() if len(data["clusters"]) else 0
        st.caption(f"{cluster_count} clusters covering {covered} wallets from pairwise timing/counterparty similarity.")


if __name__ == "__main__":
    main()
