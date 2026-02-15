"""
Frederick Platform — Streamlit Recreation
Recreates the React frontend (Next.js + Tailwind) as a single Streamlit application.
Pages: Home (Chat), Dashboard, Graph Visualization, Performance Metrics,
       File Upload, Semantic Mapping, Feedback Portal, Settings.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import math
import time
import json
import hashlib
from datetime import datetime, timedelta

# ──────────────────────────────────────────────
# Page config & custom CSS
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Frederick Platform",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Compact, clean styling inspired by the React Tailwind design
st.markdown("""
<style>
    /* Tighten main padding */
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    /* Metric cards */
    .metric-card {
        background: white; border-radius: 1rem; padding: 1.25rem;
        border: 1px solid #e2e8f0; margin-bottom: 0.5rem;
    }
    .metric-card h4 { color: #64748b; font-size: 0.85rem; margin: 0 0 0.5rem 0; font-weight: 500; }
    .metric-card .value { font-size: 1.5rem; font-weight: 600; color: #0f172a; }
    .metric-card .change-up { font-size: 0.75rem; color: #059669; background: #d1fae5; padding: 2px 8px; border-radius: 9999px; }
    .metric-card .change-down { font-size: 0.75rem; color: #dc2626; background: #fee2e2; padding: 2px 8px; border-radius: 9999px; }
    /* Activity rows */
    .activity-row {
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.75rem 1rem; background: #f8fafc; border-radius: 0.75rem; margin-bottom: 0.35rem;
    }
    .activity-row .left { display: flex; align-items: center; gap: 1rem; }
    .badge-success { font-size: 0.65rem; background: #d1fae5; color: #059669; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-warning { font-size: 0.65rem; background: #fef3c7; color: #d97706; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-error   { font-size: 0.65rem; background: #fee2e2; color: #dc2626; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-pending { font-size: 0.65rem; background: #f1f5f9; color: #64748b; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-reviewing { font-size: 0.65rem; background: #fef3c7; color: #d97706; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-done    { font-size: 0.65rem; background: #d1fae5; color: #059669; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-running { font-size: 0.65rem; background: #dbeafe; color: #2563eb; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-completed { font-size: 0.65rem; background: #d1fae5; color: #059669; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-failed  { font-size: 0.65rem; background: #fee2e2; color: #dc2626; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-high    { font-size: 0.65rem; background: #d1fae5; color: #059669; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-medium  { font-size: 0.65rem; background: #fef3c7; color: #d97706; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-low     { font-size: 0.65rem; background: #f1f5f9; color: #64748b; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    /* Sidebar style overrides */
    section[data-testid="stSidebar"] > div { padding-top: 1rem; }
    /* Chat messages */
    .chat-user { background: #ecfeff; border-radius: 1rem; padding: 0.75rem 1rem; margin: 0.5rem 0; max-width: 85%; margin-left: auto; }
    .chat-assistant { background: transparent; border-radius: 1rem; padding: 0.75rem 1rem; margin: 0.5rem 0; max-width: 85%; }
    /* Source tag pills */
    .source-pill {
        display: inline-block; font-size: 0.75rem; padding: 4px 10px;
        border-radius: 0.5rem; margin: 2px; font-weight: 500;
    }
    .source-active { background: #0891b2; color: white; }
    .source-inactive { background: #f1f5f9; color: #64748b; }
    /* Subtle dividers */
    hr { border: none; border-top: 1px solid #e2e8f0; margin: 1rem 0; }
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Quick stats in sidebar */
    .quick-stat { background: white; border-radius: 0.5rem; padding: 0.6rem 0.75rem; }
    .quick-stat .label { font-size: 0.8rem; color: #64748b; }
    .quick-stat .val { font-size: 1.2rem; font-weight: 600; color: #0f172a; }
    .quick-stat .sub { font-size: 0.65rem; color: #64748b; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Session state initialisation
# ──────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "settings" not in st.session_state:
    st.session_state.settings = {
        "dark_mode": False,
        "notifications": True,
        "api_endpoint": "https://api.frederick.ai",
    }

# ──────────────────────────────────────────────
# Sidebar — mirrors AppSidebar.tsx
# ──────────────────────────────────────────────
PAGES = {
    "Home": "🏠",
    "Dashboard": "📊",
    "Graph Visualization": "🕸️",
    "Performance Metrics": "📈",
    "File Upload": "📤",
    "Semantic Mapping": "🎯",
    "Feedback Portal": "💬",
    "Settings": "⚙️",
}

with st.sidebar:
    st.markdown("### 🧬 Frederick Platform")
    st.caption("Terminology Intelligence System")
    st.markdown("---")
    for page_name, icon in PAGES.items():
        if st.button(f"{icon}  {page_name}", key=f"nav_{page_name}", use_container_width=True,
                      type="primary" if st.session_state.page == page_name else "secondary"):
            st.session_state.page = page_name
            st.rerun()

    st.markdown("---")
    st.markdown("**Quick stats**")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="quick-stat"><div class="label">Active users</div><div class="val">2,847</div><div class="sub">↑ 12%</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="quick-stat"><div class="label">Documents</div><div class="val">15.2K</div><div class="sub">↑ 8%</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("📥  Export Data", use_container_width=True):
        st.toast("Data export initiated (dev)...")


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def metric_card(label, value, change, trend="up", help_text=""):
    """Render a styled KPI card."""
    cls = "change-up" if trend == "up" else "change-down"
    arrow = "↑" if trend == "up" else "↓"
    title_attr = f'title="{help_text}"' if help_text else ""
    st.markdown(f"""
    <div class="metric-card" {title_attr}>
        <h4>{label}</h4>
        <div style="display:flex;align-items:flex-end;justify-content:space-between;">
            <span class="value">{value}</span>
            <span class="{cls}">{arrow} {change}</span>
        </div>
    </div>""", unsafe_allow_html=True)


def deterministic_hash(s: str) -> float:
    """Same deterministic hash as the React code for stable mock data."""
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return (h % 100000) / 100000


# ═════════════════════════════════════════════
# PAGE: Home (Chat)
# ═════════════════════════════════════════════
def page_home():
    st.markdown("## How can I help you today?")
    st.caption("Ask about semantic mappings, terminology, or explore our features")

    # Category quick-links (mirrors the 6-card grid in React Home)
    categories = [
        ("Dashboard", "View metrics and overview"),
        ("Graph Visualization", "Explore Neo4j knowledge graph"),
        ("Performance Metrics", "Analyze and compare mapping results"),
        ("File Upload", "Upload files to generate mappings"),
        ("Semantic Mapping", "Map your own terms"),
        ("Feedback Portal", "Submit expert feedback"),
    ]
    cols = st.columns(3)
    for i, (name, desc) in enumerate(categories):
        with cols[i % 3]:
            if st.button(f"**{name}**\n\n{desc}", key=f"home_nav_{name}", use_container_width=True):
                st.session_state.page = name
                st.rerun()

    st.markdown("---")

    # Chat area
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Suggested prompts (only when chat is empty)
    if not st.session_state.chat_messages:
        suggested = [
            "Tell me more about semantic mapping in medical terminology",
            "Explain common terminology mapping approaches",
            "Help me understand Neo4j graph relationships",
        ]
        for prompt in suggested:
            if st.button(f"🔍  {prompt}", key=f"suggest_{prompt[:20]}", use_container_width=True):
                st.session_state.chat_messages.append({"role": "user", "content": prompt})
                st.rerun()

    # Chat input
    if user_input := st.chat_input("Ask anything about your knowledge base"):
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        # Demo response (same pattern as React buildDemoAnswer)
        short = user_input[:20]
        reply = (
            f"Based on the knowledge base, here's what I found:\n\n"
            f"**Relevant Documents:** 3 matches found\n\n"
            f"- **Document A** (95% relevance): Contains information about {short}...\n"
            f"- **Document B** (87% relevance): Related context on the topic\n"
            f"- **Document C** (76% relevance): Supporting information\n\n"
            f"**Answer:** This is a simulated response to your query about \"{short}\". "
            f"In a real implementation, this would retrieve relevant information from your vector "
            f"database and provide a synthesized answer based on your documents.\n\n"
            f"**Confidence Score:** 92% · **Sources:** [Doc-2847], [Doc-3921], [Doc-1052]"
        )
        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        st.rerun()


# ═════════════════════════════════════════════
# PAGE: Dashboard
# ═════════════════════════════════════════════
def page_dashboard():
    st.markdown("## Frederick Dashboard")
    st.caption("Overview of system performance and activity.")

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Total Queries", "45,392", "+15.3%", "up", "Total queries processed this month")
    with c2: metric_card("Graph Nodes", "8,247", "+523", "up", "Total nodes in knowledge graph")
    with c3: metric_card("Accuracy", "94.2%", "+2.1%", "up", "Model accuracy score")
    with c4: metric_card("Response Time", "0.34s", "-0.08s", "down", "Average response time")

    # Charts row
    col_chart, col_pie = st.columns([2, 1])

    with col_chart:
        st.markdown("##### Query Volume")
        dates = [(datetime(2025, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
        queries = [1200 + (i * 37 % 800) + i * 10 for i in range(30)]
        successful = [1100 + (i * 29 % 800) + i * 9 for i in range(30)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=queries, name="Total Queries", line=dict(color="#374151", width=2), marker=dict(size=4), mode="lines+markers"))
        fig.add_trace(go.Scatter(x=dates, y=successful, name="Successful", line=dict(color="#10b981", width=2), marker=dict(size=4), mode="lines+markers"))
        fig.update_layout(height=320, margin=dict(l=40, r=20, t=20, b=40), legend=dict(orientation="h", y=-0.15), xaxis=dict(gridcolor="#f3f4f6"), yaxis=dict(gridcolor="#f3f4f6"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col_pie:
        st.markdown("##### Query Categories")
        fig_pie = go.Figure(data=[go.Pie(
            labels=["Search", "Analysis", "Visualization", "Export", "Other"],
            values=[35, 28, 20, 12, 5], hole=0.5,
            marker=dict(colors=["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#6b7280"]),
            textinfo="percent",
        )])
        fig_pie.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_pie, use_container_width=True)

    # Recent Activity
    st.markdown("##### Recent Activity")
    activities = [
        ("10:00 AM", "Alice Chen", "Uploaded dataset", "success"),
        ("10:30 AM", "Bob Smith", "Ran analysis", "success"),
        ("11:00 AM", "Carol Davis", "Created visualization", "warning"),
        ("11:30 AM", "David Lee", "Exported report", "success"),
        ("12:00 PM", "Emma Wilson", "Updated model", "success"),
    ]
    for t, user, action, status in activities:
        badge = f'<span class="badge-{status}">{status.capitalize()}</span>'
        st.markdown(f"""<div class="activity-row">
            <div class="left">
                <span style="font-size:0.75rem;color:#94a3b8;width:4rem;">{t}</span>
                <span style="font-size:0.85rem;font-weight:500;color:#0f172a;width:7rem;">{user}</span>
                <span style="font-size:0.85rem;color:#64748b;">{action}</span>
            </div>{badge}</div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════
# PAGE: Semantic Mapping
# ═════════════════════════════════════════════
def page_semantic_mapping():
    st.markdown("## Semantic Mapping")
    st.caption("Map medical terms to standardized terminology systems.")

    SOURCES = ["SNOMED CT", "ICD-10", "LOINC", "RxNorm", "MedDRA", "NCI"]

    main_col, side_col = st.columns([2, 1])

    with main_col:
        query = st.text_area("Terms to map", placeholder="Enter terms, one per line...\n\nExample:\nHypertension\nType 2 Diabetes\nAspirin", height=140)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Load example"):
                st.session_state["_sm_query"] = "Hypertension\nType 2 Diabetes\nAspirin\nAtrial Fibrillation"
                st.rerun()

        # Direction
        direction = st.radio("Direction", ["Forward", "Bidirectional"], horizontal=True)

        # Threshold
        threshold = st.slider("Threshold", 0.50, 1.00, 0.70, 0.05)

        # Sources toggle
        st.markdown("**Sources**")
        selected_sources = []
        src_cols = st.columns(len(SOURCES))
        for i, src in enumerate(SOURCES):
            with src_cols[i]:
                if st.checkbox(src, value=(src in ["SNOMED CT", "ICD-10", "LOINC"]), key=f"src_{src}"):
                    selected_sources.append(src)

        run = st.button("🎯  Map Terms", type="primary", disabled=not query.strip())

        # Results
        if run and query.strip():
            terms = [t.strip() for t in query.strip().split("\n") if t.strip()]
            sources = selected_sources if selected_sources else SOURCES
            match_types = ["Exact", "Synonym", "Broader", "Narrower", "Related"]
            results = []
            for term in terms:
                for i in range(3):
                    score = 0.6 + deterministic_hash(f"{term}:{i}") * 0.4
                    if score < threshold:
                        continue
                    conf = "high" if score >= 0.9 else ("medium" if score >= 0.75 else "low")
                    source = sources[i % len(sources)]
                    concept_id = f"C{int(100000 + deterministic_hash(f'{term}:cid:{i}') * 900000)}"
                    results.append({
                        "Source Term": term,
                        "Mapped Term": f'{source} concept for "{term}"',
                        "Match": match_types[i % len(match_types)],
                        "Score": round(score, 3),
                        "Confidence": conf,
                        "Source": source,
                        "Concept ID": concept_id,
                    })
            results.sort(key=lambda r: r["Score"], reverse=True)
            results = results[:20]
            st.session_state["_sm_results"] = results

        if "_sm_results" in st.session_state and st.session_state["_sm_results"]:
            results = st.session_state["_sm_results"]
            st.markdown("##### Results")
            exp_col, clr_col = st.columns([1, 1])
            with exp_col:
                csv_data = pd.DataFrame(results).to_csv(index=False)
                st.download_button("📥 Export CSV", csv_data, "mapping_results.csv", "text/csv")
            with clr_col:
                if st.button("✕ Clear"):
                    st.session_state["_sm_results"] = []
                    st.rerun()

            for r in results:
                badge = f'<span class="badge-{r["Confidence"]}">{r["Confidence"].capitalize()}</span>'
                st.markdown(f"""<div class="activity-row">
                    <div class="left" style="flex-direction:column;align-items:flex-start;gap:0.25rem;">
                        <span style="font-size:0.85rem;font-weight:500;color:#0f172a;">{r["Source Term"]}</span>
                        <span style="font-size:0.8rem;color:#64748b;">{r["Mapped Term"]}</span>
                        <span style="font-size:0.7rem;color:#94a3b8;">{r["Match"]} · {r["Source"]} · <code>{r["Concept ID"]}</code></span>
                    </div>
                    <div style="display:flex;align-items:center;gap:0.5rem;">
                        <span style="font-size:0.75rem;color:#94a3b8;">{r["Score"]:.2f}</span>
                        {badge}
                    </div>
                </div>""", unsafe_allow_html=True)

    with side_col:
        # Summary
        if "_sm_results" in st.session_state and st.session_state["_sm_results"]:
            results = st.session_state["_sm_results"]
            avg_score = sum(r["Score"] for r in results) / len(results)
            high_conf = sum(1 for r in results if r["Confidence"] == "high")
            unique_sources = len(set(r["Source"] for r in results))
            st.markdown("##### Summary")
            st.markdown(f"**Total mappings:** {len(results)}")
            st.markdown(f"**Avg score:** {avg_score:.3f}")
            st.markdown(f"**High confidence:** {high_conf}")
            st.markdown(f"**Sources used:** {unique_sources}")

        st.markdown("##### Supported Sources")
        pills_html = " ".join(f'<span class="source-pill source-inactive">{s}</span>' for s in SOURCES)
        st.markdown(pills_html, unsafe_allow_html=True)

        st.markdown("##### Tips")
        st.markdown("- Enter one term per line\n- Higher threshold = stricter matches\n- Select multiple sources for broader coverage")


# ═════════════════════════════════════════════
# PAGE: Graph Visualization
# ═════════════════════════════════════════════
def page_graph():
    st.markdown("## Graph Visualization")
    st.caption("Interactive knowledge graph explorer with Cypher query builder.")

    main_col, side_col = st.columns([3, 1])

    with side_col:
        node_type = st.selectbox("Node Type", ["All", "Person", "Document", "Concept", "Organization"])
        layout_type = st.selectbox("Layout", ["Force-directed", "Circular", "Hierarchical", "Random"])
        depth = st.slider("Depth", 1, 5, 2)
        max_nodes = st.number_input("Max Nodes", 10, 100, 50, step=10)
        search_term = st.text_input("🔍 Search Nodes")

        with st.expander("Cypher Query Builder"):
            cypher = st.text_area("Query", "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 25", height=100)
            if st.button("📋 Copy Query"):
                st.code(cypher, language="cypher")
                st.toast("Query displayed — copy from above.")

    with main_col:
        # Generate graph
        node_types_all = ["Person", "Document", "Concept", "Organization"]
        type_colors = {"Person": "#4fc3f7", "Document": "#4caf50", "Concept": "#ff9800", "Organization": "#9c27b0"}
        allowed = node_types_all if node_type == "All" else [node_type]

        np.random.seed(42)
        num_nodes = min(int(max_nodes), 50)
        nodes = []
        for i in range(num_nodes):
            t = allowed[i % len(allowed)]
            nodes.append({"name": f"{t}_{i+1}", "type": t, "color": type_colors[t]})

        # Positions
        positions = {}
        if layout_type == "Circular":
            for i, n in enumerate(nodes):
                angle = 2 * math.pi * i / len(nodes)
                positions[n["name"]] = (math.cos(angle), math.sin(angle))
        elif layout_type == "Hierarchical":
            levels = 4
            per_level = max(1, len(nodes) // levels)
            for i, n in enumerate(nodes):
                lv = i // per_level
                pos = i % per_level
                x = (pos * 2.0) / per_level - 1
                y = 1 - (lv * 2.0) / levels
                positions[n["name"]] = (x, y)
        elif layout_type == "Force-directed":
            for n in nodes:
                positions[n["name"]] = ((np.random.random() - 0.5) * 4, (np.random.random() - 0.5) * 4)
            for _ in range(8):
                for i in range(len(nodes)):
                    for j in range(i + 1, len(nodes)):
                        a = list(positions[nodes[i]["name"]])
                        b = list(positions[nodes[j]["name"]])
                        dx, dy = a[0] - b[0], a[1] - b[1]
                        dist = math.sqrt(dx * dx + dy * dy) + 0.01
                        if dist < 1:
                            force = (1 - dist) * 0.05
                            a[0] += (dx / dist) * force; a[1] += (dy / dist) * force
                            b[0] -= (dx / dist) * force; b[1] -= (dy / dist) * force
                        positions[nodes[i]["name"]] = tuple(a)
                        positions[nodes[j]["name"]] = tuple(b)
        else:
            for n in nodes:
                positions[n["name"]] = ((np.random.random() - 0.5) * 3, (np.random.random() - 0.5) * 3)

        # Edges
        edges = []
        for i in range(len(nodes)):
            conns = min(4, max(1, np.random.randint(1, 5)))
            for _ in range(conns):
                j = np.random.randint(0, len(nodes))
                if i != j:
                    src, tgt = nodes[i]["name"], nodes[j]["name"]
                    if not any((e["source"] == src and e["target"] == tgt) or (e["source"] == tgt and e["target"] == src) for e in edges):
                        edges.append({"source": src, "target": tgt, "similarity": np.random.random()})

        # Build Plotly figure
        fig = go.Figure()

        # Edges
        edge_x, edge_y = [], []
        for e in edges:
            if e["source"] in positions and e["target"] in positions:
                x0, y0 = positions[e["source"]]
                x1, y1 = positions[e["target"]]
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1, color="rgba(180,180,180,0.25)"), hoverinfo="none", showlegend=False))

        # Nodes
        node_x = [positions[n["name"]][0] for n in nodes]
        node_y = [positions[n["name"]][1] for n in nodes]
        node_colors = [n["color"] for n in nodes]
        node_names = [n["name"] for n in nodes]
        node_hover = [f'{n["name"]} ({n["type"]})' for n in nodes]

        # Filter for search highlights
        highlighted = []
        if search_term.strip():
            highlighted = [n["name"] for n in nodes if search_term.lower() in n["name"].lower()]

        marker_sizes = [18 if n["name"] in highlighted else 12 for n in nodes]
        marker_line_widths = [3 if n["name"] in highlighted else 1 for n in nodes]
        marker_line_colors = ["#22d3ee" if n["name"] in highlighted else "#ffffff" for n in nodes]

        fig.add_trace(go.Scatter(
            x=node_x, y=node_y, mode="markers+text", text=node_names, textposition="top center",
            hovertext=node_hover, hoverinfo="text",
            marker=dict(size=marker_sizes, color=node_colors, line=dict(width=marker_line_widths, color=marker_line_colors)),
            textfont=dict(size=8, color="#374151"),
            showlegend=False,
        ))

        fig.update_layout(
            height=600, showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            hovermode="closest",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Legend
        legend_cols = st.columns(4)
        for i, (tp, col) in enumerate(type_colors.items()):
            with legend_cols[i]:
                st.markdown(f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{col};margin-right:4px;"></span> {tp}', unsafe_allow_html=True)

        # Search results
        if search_term.strip() and highlighted:
            st.info(f"Found **{len(highlighted)}** matching nodes: {', '.join(highlighted[:8])}{'...' if len(highlighted) > 8 else ''}")
        elif search_term.strip():
            st.warning("No matching nodes found.")


# ═════════════════════════════════════════════
# PAGE: File Upload
# ═════════════════════════════════════════════
def page_file_upload():
    st.markdown("## Upload Files")
    st.caption("Upload training data, validation sets, or knowledge base files.")

    UPLOAD_TYPES = ["Training", "Validation", "Test", "Knowledge Base"]
    MODELS = ["RAG Model v2.0", "Classification v1.5", "NER v3.0", "Custom"]

    main_col, side_col = st.columns([2, 1])

    with main_col:
        # Config
        upload_type = st.radio("Data type", UPLOAD_TYPES, horizontal=True)
        target_model = st.radio("Target model", MODELS, horizontal=True)

        st.markdown("---")

        # Dropzone
        uploaded_files = st.file_uploader(
            "Drop files or click to browse",
            type=["pdf", "txt", "csv", "json", "doc", "docx", "xlsx"],
            accept_multiple_files=True,
            help="CSV, JSON, TXT, PDF, XLSX — Max 50MB per file",
        )

        if uploaded_files:
            total_size = sum(f.size for f in uploaded_files)
            size_str = f"{total_size / 1024:.1f} KB" if total_size < 1_048_576 else f"{total_size / 1_048_576:.1f} MB"
            st.markdown(f"**{len(uploaded_files)} file(s)** · {size_str}")

            for f in uploaded_files:
                fsize = f"{f.size / 1024:.1f} KB" if f.size < 1_048_576 else f"{f.size / 1_048_576:.1f} MB"
                st.markdown(f"📄 **{f.name}** — {fsize}")

            if st.button("📤 Upload", type="primary"):
                progress = st.progress(0, text="Uploading...")
                for i in range(100):
                    time.sleep(0.02)
                    progress.progress(i + 1, text=f"Uploading... {i + 1}%")
                st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")

    with side_col:
        st.markdown("##### Recent Jobs")
        jobs = [
            ("TRN-0846", "RAG Model v2.0", 12, "completed", "Jan 20"),
            ("TRN-0845", "Classification v1.5", 8, "running", "Jan 19"),
            ("TRN-0844", "NER v3.0", 15, "completed", "Jan 18"),
            ("TRN-0843", "RAG Model v1.9", 10, "failed", "Jan 17"),
        ]
        for jid, model, files, status, date in jobs:
            badge = f'<span class="badge-{status}">{status.capitalize()}</span>'
            st.markdown(f"""<div style="background:#f8fafc;border-radius:0.75rem;padding:0.75rem;margin-bottom:0.35rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:0.85rem;font-weight:500;color:#0f172a;">{model}</span>
                    {badge}
                </div>
                <span style="font-size:0.7rem;color:#94a3b8;">{jid} · {files} files · {date}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("##### Accepted Formats")
        st.markdown(" ".join(f'<span class="source-pill source-inactive">{e}</span>' for e in ["CSV", "JSON", "TXT", "PDF", "XLSX"]), unsafe_allow_html=True)

        st.markdown("##### Tips")
        st.markdown("- Use CSV for structured term lists\n- JSON supports nested relationships\n- Max file size: 50MB per file")


# ═════════════════════════════════════════════
# PAGE: SME Feedback
# ═════════════════════════════════════════════
def page_feedback():
    st.markdown("## Submit Feedback")
    st.caption("Report issues or suggest improvements to terminology mappings.")

    TYPES = ["Incorrect mapping", "Missing term", "Suggestion", "Relationship", "Platform", "Other"]
    PRIORITIES = ["low", "medium", "high", "critical"]

    if "feedback_sent" not in st.session_state:
        st.session_state.feedback_sent = False

    if st.session_state.feedback_sent:
        st.success(f"✅ **Submitted!** Reference: FB-{np.random.randint(100, 999)}")
        if st.button("Submit another"):
            st.session_state.feedback_sent = False
            st.rerun()
        return

    main_col, side_col = st.columns([2, 1])

    with main_col:
        with st.form("feedback_form"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Name")
            with c2:
                email = st.text_input("Email")

            issue_type = st.selectbox("Issue type", TYPES)
            priority = st.select_slider("Priority", options=PRIORITIES, value="medium")
            subject = st.text_input("Subject", placeholder="Brief summary")

            c3, c4 = st.columns(2)
            with c3:
                term_ref = st.text_input("Term reference (optional)")
            with c4:
                concept_id = st.text_input("Concept ID (optional)")

            description = st.text_area("Description", placeholder="What happened? What did you expect?", height=120)
            char_count = len(description.strip())
            if char_count < 30:
                st.caption(f"{char_count}/30 characters")
            else:
                st.caption(f"✅ {char_count}/30 characters")

            attachments = st.file_uploader("Attach files", accept_multiple_files=True, key="fb_files")

            submitted = st.form_submit_button("Submit →", type="primary")
            if submitted:
                errors = []
                if not name.strip():
                    errors.append("Name is required")
                if not email.strip() or "@" not in email:
                    errors.append("Valid email is required")
                if not subject.strip():
                    errors.append("Subject is required")
                if char_count < 30:
                    errors.append("Description must be at least 30 characters")
                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    st.session_state.feedback_sent = True
                    st.rerun()

    with side_col:
        st.markdown("##### Recent Submissions")
        history = [
            ("FB-234", "SNOMED mapping for atrial fibrillation", "reviewing", "Jan 19"),
            ("FB-198", "CAR-T cell therapy terminology", "done", "Jan 17"),
            ("FB-156", "HTN synonym for Hypertension", "done", "Jan 15"),
            ("FB-142", "Drug interaction hierarchy error", "pending", "Jan 12"),
        ]
        for fid, subj, status, date in history:
            badge = f'<span class="badge-{status}">{"In Review" if status == "reviewing" else ("Resolved" if status == "done" else "Pending")}</span>'
            st.markdown(f"""<div style="background:#f8fafc;border-radius:0.75rem;padding:0.75rem;margin-bottom:0.35rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:0.85rem;font-weight:500;color:#0f172a;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:200px;">{subj}</span>
                    {badge}
                </div>
                <span style="font-size:0.7rem;color:#94a3b8;">{fid} · {date}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("##### Tips")
        st.markdown("- Include concept IDs when possible\n- Be specific about expected behavior\n- Attach screenshots for complex issues")


# ═════════════════════════════════════════════
# PAGE: Results / Performance Metrics
# ═════════════════════════════════════════════
def page_results_analysis():
    st.markdown("## Performance Metrics")
    st.caption("Monitor system performance, usage, and resource utilization.")

    # Date range
    dc1, dc2, dc3, dc4 = st.columns([2, 2, 1, 1])
    with dc1:
        start_date = st.date_input("Start date", datetime.now() - timedelta(days=30))
    with dc2:
        end_date = st.date_input("End date", datetime.now())
    with dc3:
        if st.button("🔄 Refresh Metrics", type="primary"):
            st.rerun()
    with dc4:
        if st.button("📥 Export Data"):
            st.toast("Export initiated...")

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Avg Response Time", "0.34s", "-12%", "down", "Average query response time")
    with c2: metric_card("Success Rate", "94.2%", "+2.1%", "up", "Percentage of successful queries")
    with c3: metric_card("Active Sessions", "127", "+15", "up", "Current active user sessions")
    with c4: metric_card("Error Rate", "0.8%", "-0.3%", "down", "Percentage of failed requests")

    # Tabs
    tab_perf, tab_usage, tab_errors, tab_resources = st.tabs(["📊 Performance", "📈 Usage", "⚠️ Errors", "🖥️ Resources"])

    with tab_perf:
        pc1, pc2 = st.columns(2)
        with pc1:
            st.markdown("##### Response Time Distribution")
            resp_times = np.exp(np.random.normal(0, 0.5, 1000))
            fig_hist = go.Figure(data=[go.Histogram(x=resp_times, nbinsx=30, marker_color="#4fc3f7")])
            fig_hist.update_layout(height=300, margin=dict(l=50, r=30, t=20, b=50), xaxis_title="Response Time (s)", yaxis_title="Frequency", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(gridcolor="#e5e7eb"), yaxis=dict(gridcolor="#e5e7eb"))
            st.plotly_chart(fig_hist, use_container_width=True)

        with pc2:
            st.markdown("##### Throughput Over Time")
            hours = list(range(24))
            throughput = [800 + np.random.randint(0, 400) + h * 10 for h in hours]
            fig_bar = go.Figure(data=[go.Bar(x=hours, y=throughput, marker_color="#4caf50")])
            fig_bar.update_layout(height=300, margin=dict(l=50, r=30, t=20, b=50), xaxis_title="Hour of Day", yaxis_title="Requests/Hour", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(gridcolor="#e5e7eb"), yaxis=dict(gridcolor="#e5e7eb"))
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab_usage:
        st.markdown("##### API Usage Statistics")
        endpoint_stats = pd.DataFrame([
            {"Endpoint": "/search", "Calls": "15,234", "Avg Time (ms)": 234, "Success Rate": "99.2%"},
            {"Endpoint": "/analyze", "Calls": "8,921", "Avg Time (ms)": 567, "Success Rate": "97.8%"},
            {"Endpoint": "/graph", "Calls": "6,547", "Avg Time (ms)": 890, "Success Rate": "95.3%"},
            {"Endpoint": "/upload", "Calls": "3,210", "Avg Time (ms)": 123, "Success Rate": "99.9%"},
            {"Endpoint": "/export", "Calls": "1,876", "Avg Time (ms)": 456, "Success Rate": "98.1%"},
        ])
        st.dataframe(endpoint_stats, use_container_width=True, hide_index=True)

    with tab_errors:
        ec1, ec2 = st.columns([2, 1])
        with ec1:
            st.markdown("##### Error Analysis")
            error_stats = pd.DataFrame([
                {"Error Type": "Timeout", "Count": 45, "Percentage": "16.7%"},
                {"Error Type": "Bad Request", "Count": 123, "Percentage": "45.6%"},
                {"Error Type": "Server Error", "Count": 12, "Percentage": "4.4%"},
                {"Error Type": "Not Found", "Count": 67, "Percentage": "24.8%"},
                {"Error Type": "Auth Failed", "Count": 23, "Percentage": "8.5%"},
            ])
            st.dataframe(error_stats, use_container_width=True, hide_index=True)

        with ec2:
            fig_err = go.Figure(data=[go.Pie(
                labels=["Timeout", "Bad Request", "Server Error", "Not Found", "Auth Failed"],
                values=[45, 123, 12, 67, 23], hole=0.4,
                marker=dict(colors=["#ef4444", "#f59e0b", "#eab308", "#84cc16", "#22c55e"]),
            )])
            fig_err.update_layout(height=250, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig_err, use_container_width=True)

    with tab_resources:
        st.markdown("##### System Resources")
        rc1, rc2 = st.columns(2)
        with rc1:
            cpu = [40 + np.random.randint(0, 40) for _ in range(60)]
            fig_cpu = go.Figure(data=[go.Scatter(y=cpu, mode="lines", line=dict(color="#ff9800", width=2))])
            fig_cpu.update_layout(title="CPU Usage (%)", height=250, margin=dict(l=50, r=30, t=40, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(gridcolor="#e5e7eb", showticklabels=False), yaxis=dict(gridcolor="#e5e7eb"), showlegend=False)
            st.plotly_chart(fig_cpu, use_container_width=True)

        with rc2:
            mem = [50 + np.random.randint(0, 20) for _ in range(60)]
            fig_mem = go.Figure(data=[go.Scatter(y=mem, mode="lines", line=dict(color="#9c27b0", width=2))])
            fig_mem.update_layout(title="Memory Usage (%)", height=250, margin=dict(l=50, r=30, t=40, b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(gridcolor="#e5e7eb", showticklabels=False), yaxis=dict(gridcolor="#e5e7eb"), showlegend=False)
            st.plotly_chart(fig_mem, use_container_width=True)


# ═════════════════════════════════════════════
# PAGE: Settings
# ═════════════════════════════════════════════
def page_settings():
    st.markdown("## Settings")
    st.caption("Configure your application preferences and settings.")

    settings = st.session_state.settings

    st.markdown("##### 🌓 Theme")
    st.caption("Switch between light and dark mode")
    dark = st.toggle("Dark Mode", value=settings["dark_mode"])
    settings["dark_mode"] = dark

    st.markdown("---")

    st.markdown("##### 🔔 Notifications")
    st.caption("Enable or disable system notifications")
    notif = st.toggle("Notifications", value=settings["notifications"])
    settings["notifications"] = notif

    st.markdown("---")

    st.markdown("##### 🖥️ API Endpoint")
    st.caption("Configure the backend API URL")
    endpoint = st.text_input("API Endpoint", value=settings["api_endpoint"])
    settings["api_endpoint"] = endpoint
    st.caption("Changes will take effect on next API call")

    st.markdown("---")
    if st.button("💾 Save Changes", type="primary"):
        st.session_state.settings = settings
        st.success("Settings saved!")


# ──────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────
page = st.session_state.page

if page == "Home":
    page_home()
elif page == "Dashboard":
    page_dashboard()
elif page == "Semantic Mapping":
    page_semantic_mapping()
elif page == "Graph Visualization":
    page_graph()
elif page == "File Upload":
    page_file_upload()
elif page == "Feedback Portal":
    page_feedback()
elif page == "Performance Metrics":
    page_results_analysis()
elif page == "Settings":
    page_settings()

# Footer
st.markdown("---")
st.caption("Frederick Platform (Streamlit) v1.0.0 | Powered by RAG & Neo4j | © 2025 Frederick AI")
