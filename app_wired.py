"""
Frederick Platform — Streamlit Frontend (Wired to Neo4j)
========================================================
Recreates the React frontend and connects to the live ncit-semantic-mapper
backend via backend_client.py.

When Neo4j is reachable:
  - Semantic Mapping uses real exact_match / synonym / semantic search
  - Graph Visualization pulls real nodes + edges from Neo4j
  - Home chat uses the LangChain ReAct agent (if initialised)

When Neo4j is unreachable:
  - All pages fall back to the same mock/demo data as the React version
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import math
import time
from datetime import datetime, timedelta
from typing import Optional

from backend_client import get_client, BackendClient, MatchResult, GraphPayload

# ──────────────────────────────────────────────
# Page config & CSS (same as before — collapsed for brevity)
# ──────────────────────────────────────────────
st.set_page_config(page_title="Frederick Platform", page_icon="🧬", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .metric-card {
        background: white; border-radius: 1rem; padding: 1.25rem;
        border: 1px solid #e2e8f0; margin-bottom: 0.5rem;
    }
    .metric-card h4 { color: #64748b; font-size: 0.85rem; margin: 0 0 0.5rem 0; font-weight: 500; }
    .metric-card .value { font-size: 1.5rem; font-weight: 600; color: #0f172a; }
    .metric-card .change-up { font-size: 0.75rem; color: #059669; background: #d1fae5; padding: 2px 8px; border-radius: 9999px; }
    .metric-card .change-down { font-size: 0.75rem; color: #dc2626; background: #fee2e2; padding: 2px 8px; border-radius: 9999px; }
    .activity-row {
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.75rem 1rem; background: #f8fafc; border-radius: 0.75rem; margin-bottom: 0.35rem;
    }
    .activity-row .left { display: flex; align-items: center; gap: 1rem; }
    .badge-success, .badge-completed, .badge-high, .badge-done { font-size: 0.65rem; background: #d1fae5; color: #059669; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-warning, .badge-reviewing, .badge-medium { font-size: 0.65rem; background: #fef3c7; color: #d97706; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-error, .badge-failed { font-size: 0.65rem; background: #fee2e2; color: #dc2626; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-pending, .badge-low { font-size: 0.65rem; background: #f1f5f9; color: #64748b; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .badge-running { font-size: 0.65rem; background: #dbeafe; color: #2563eb; padding: 2px 8px; border-radius: 9999px; font-weight: 500; }
    .source-pill { display: inline-block; font-size: 0.75rem; padding: 4px 10px; border-radius: 0.5rem; margin: 2px; font-weight: 500; }
    .source-active { background: #0891b2; color: white; }
    .source-inactive { background: #f1f5f9; color: #64748b; }
    .quick-stat { background: white; border-radius: 0.5rem; padding: 0.6rem 0.75rem; }
    .quick-stat .label { font-size: 0.8rem; color: #64748b; }
    .quick-stat .val { font-size: 1.2rem; font-weight: 600; color: #0f172a; }
    .quick-stat .sub { font-size: 0.65rem; color: #64748b; }
    hr { border: none; border-top: 1px solid #e2e8f0; margin: 1rem 0; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "settings" not in st.session_state:
    st.session_state.settings = {"dark_mode": False, "notifications": True, "api_endpoint": "https://api.frederick.ai"}
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = (
        "You are an expert medical data mapper specializing in NCIT (National Cancer Institute Thesaurus) terminology.\n"
        "Your job is to help map raw medical data values to standardized NCIT terms and codes.\n"
        "Be thorough but concise in your analysis. Always provide the recommended NCIT code and term if found."
    )
if "sme_results" not in st.session_state:
    st.session_state.sme_results = None
if "sme_grades" not in st.session_state:
    st.session_state.sme_grades = {}
if "graph_query_history" not in st.session_state:
    st.session_state.graph_query_history = []

# ──────────────────────────────────────────────
# Backend client (cached singleton)
# ──────────────────────────────────────────────
@st.cache_resource
def _init_client() -> BackendClient:
    return get_client()

client = _init_client()

# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
PAGES = {
    "Home": "🏠", "Dashboard": "📊", "SME Workbench": "🧪",
    "Graph Query": "🔍", "Graph Visualization": "🕸️",
    "Performance Metrics": "📈", "File Upload": "📤",
    "Semantic Mapping": "🎯", "Feedback Portal": "💬", "Settings": "⚙️",
}

with st.sidebar:
    st.markdown("### 🧬 Frederick Platform")

    # ── Live backend status ──
    status = client.status_dict()
    if status["neo4j_connected"]:
        st.success("Neo4j: Connected", icon="✅")
    else:
        st.error("Neo4j: Offline (using mock data)", icon="❌")
        if status["error"]:
            st.caption(status["error"])

    cols = st.columns(3)
    with cols[0]:
        st.caption(f"Exact: {'✅' if status['exact_match_ready'] else '❌'}")
    with cols[1]:
        st.caption(f"Synonym: {'✅' if status['synonym_ready'] else '❌'}")
    with cols[2]:
        st.caption(f"Semantic: {'✅' if status['semantic_ready'] else '❌'}")

    st.caption(f"Ollama LLM: {'✅ Ready' if status.get('ollama_ready') else '⏳ Not tested yet'}")

    if not status["agent_ready"]:
        if st.button("🚀 Initialise Agent"):
            with st.spinner("Starting LangChain agent (Ollama + Neo4j)..."):
                ok = client.init_agent()
            if ok:
                st.success("Agent ready!")
            else:
                st.error(f"Agent failed: {client.error}")
    else:
        st.success("Agent: Ready", icon="🤖")

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
    cls = "change-up" if trend == "up" else "change-down"
    arrow = "↑" if trend == "up" else "↓"
    title_attr = f'title="{help_text}"' if help_text else ""
    st.markdown(f"""<div class="metric-card" {title_attr}>
        <h4>{label}</h4>
        <div style="display:flex;align-items:flex-end;justify-content:space-between;">
            <span class="value">{value}</span><span class="{cls}">{arrow} {change}</span>
        </div></div>""", unsafe_allow_html=True)


def deterministic_hash(s: str) -> float:
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return (h % 100000) / 100000


def render_match_result(r: MatchResult, idx: int = 0):
    """Render a single MatchResult as a styled card."""
    conf = "high" if r.score >= 0.9 else ("medium" if r.score >= 0.7 else "low")
    badge = f'<span class="badge-{conf}">{conf.capitalize()}</span>'
    extra_info = ""
    if r.extra:
        parts = [f"{k}: {v}" for k, v in r.extra.items() if v]
        if parts:
            extra_info = f' · {" · ".join(parts)}'
    st.markdown(f"""<div class="activity-row">
        <div class="left" style="flex-direction:column;align-items:flex-start;gap:0.25rem;">
            <span style="font-size:0.85rem;font-weight:500;color:#0f172a;">{r.term or r.code}</span>
            <span style="font-size:0.8rem;color:#64748b;">{r.definition[:120]}{'...' if len(r.definition) > 120 else ''}</span>
            <span style="font-size:0.7rem;color:#94a3b8;">{r.source} · <code>{r.code}</code> · {r.node_type}{extra_info}</span>
        </div>
        <div style="display:flex;align-items:center;gap:0.5rem;">
            <span style="font-size:0.75rem;color:#94a3b8;">{r.score:.3f}</span>
            {badge}
        </div>
    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════
# PAGE: Home (Chat) — wired to agent
# ═════════════════════════════════════════════
def page_home():
    st.markdown("## How can I help you today?")
    st.caption("Ask about semantic mappings, terminology, or explore our features")

    # ── System Prompt Editor (Sprint 11) ──
    with st.expander("⚙️ Edit System Prompt", expanded=False):
        st.caption("Customise how the AI agent responds. Changes take effect on the next query.")
        new_prompt = st.text_area(
            "System Prompt",
            value=st.session_state.system_prompt,
            height=160,
            key="home_system_prompt_editor",
            help="This prompt is sent to the LLM agent before every query. Edit it to change the agent's behaviour, focus, or style."
        )
        col_save, col_reset, col_spacer = st.columns([1, 1, 4])
        with col_save:
            if st.button("💾 Save Prompt", key="save_prompt_home"):
                st.session_state.system_prompt = new_prompt
                st.success("System prompt updated!")
        with col_reset:
            if st.button("↩️ Reset", key="reset_prompt_home"):
                st.session_state.system_prompt = (
                    "You are an expert medical data mapper specializing in NCIT (National Cancer Institute Thesaurus) terminology.\n"
                    "Your job is to help map raw medical data values to standardized NCIT terms and codes.\n"
                    "Be thorough but concise in your analysis. Always provide the recommended NCIT code and term if found."
                )
                st.rerun()

    categories = [
        ("Dashboard", "View metrics and overview"),
        ("SME Workbench", "Upload terms & grade synonym matches"),
        ("Graph Query", "Ask questions about the knowledge graph"),
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

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

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

    if user_input := st.chat_input("Ask anything about your knowledge base"):
        st.session_state.chat_messages.append({"role": "user", "content": user_input})

        # ── Try real agent, fall back to demo ──
        if client.agent_ready:
            with st.spinner("Agent is thinking..."):
                reply = client.agent_query(user_input)
        else:
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
                f"**Confidence Score:** 92% · **Sources:** [Doc-2847], [Doc-3921], [Doc-1052]\n\n"
                f"*💡 Initialise the agent in the sidebar for live Neo4j-backed answers.*"
            )

        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        st.rerun()


# ═════════════════════════════════════════════
# PAGE: Semantic Mapping — WIRED TO NEO4J
# ═════════════════════════════════════════════
def page_semantic_mapping():
    st.markdown("## Semantic Mapping")
    st.caption("Map medical terms to standardized terminology systems.")

    is_live = client.connected

    if is_live:
        st.success("🔗 Connected to live Neo4j — results are real", icon="✅")
    else:
        st.warning("⚠️ Neo4j offline — showing mock results")

    SOURCES_DISPLAY = ["SNOMED CT", "ICD-10", "LOINC", "RxNorm", "MedDRA", "NCI"]

    main_col, side_col = st.columns([2, 1])

    with main_col:
        # Handle "Load example" by setting a default before the widget renders
        if st.session_state.get("_sm_load_example"):
            st.session_state["_sm_load_example"] = False
            default_query = "Lung Carcinoma\nProstate\nDiabetes Mellitus\nAtrial Fibrillation"
        else:
            default_query = ""

        query = st.text_area("Terms to map", value=default_query, placeholder="Enter terms, one per line...\n\nExample:\nHypertension\nType 2 Diabetes\nAspirin", height=140)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Load example"):
                st.session_state["_sm_load_example"] = True
                st.rerun()

        # Search mode (only relevant when live)
        search_mode = st.radio(
            "Search strategy",
            ["Auto (exact → fuzzy → semantic)", "Exact only", "Fuzzy only", "Semantic PV", "Semantic NCIT", "Semantic CDE definition", "Semantic NCIT definition"],
            horizontal=True,
            help="Auto tries exact match first, then fuzzy, then semantic."
        )

        threshold = st.slider("Minimum score threshold", 0.0, 1.0, 0.5, 0.05)

        run = st.button("🎯  Map Terms", type="primary", disabled=not query.strip())

        if run and query.strip():
            terms = [t.strip() for t in query.strip().split("\n") if t.strip()]
            all_results: list[MatchResult] = []

            if is_live:
                progress = st.progress(0, text="Mapping terms...")
                for i, term in enumerate(terms):
                    progress.progress((i + 1) / len(terms), text=f"Mapping: {term}")

                    if search_mode.startswith("Auto"):
                        # 1) Exact match
                        r = client.exact_match_by_term(term)
                        if r:
                            all_results.append(r)
                            continue
                        # 2) Fuzzy
                        fuzzy = client.fuzzy_match(term, limit=3)
                        if fuzzy:
                            all_results.extend(fuzzy)
                            continue
                        # 3) Semantic NCIT
                        sem = client.semantic_search_ncit(term, top_k=3)
                        all_results.extend(sem)

                    elif search_mode == "Exact only":
                        r = client.exact_match_by_term(term)
                        if r:
                            all_results.append(r)
                        else:
                            r = client.exact_match_by_code(term)
                            if r:
                                all_results.append(r)

                    elif search_mode == "Fuzzy only":
                        all_results.extend(client.fuzzy_match(term, limit=5))

                    elif search_mode == "Semantic PV":
                        all_results.extend(client.semantic_search_pv(term, top_k=5))

                    elif search_mode == "Semantic NCIT":
                        all_results.extend(client.semantic_search_ncit(term, top_k=5))

                    elif search_mode == "Semantic CDE definition":
                        all_results.extend(client.semantic_search_cde_definition(term, top_k=5))

                    elif search_mode == "Semantic NCIT definition":
                        all_results.extend(client.semantic_search_ncit_definition(term, top_k=5))

                progress.empty()
            else:
                # ── Mock fallback (same as original app.py) ──
                match_types = ["Exact", "Synonym", "Broader", "Narrower", "Related"]
                for term in terms:
                    for i in range(3):
                        score = 0.6 + deterministic_hash(f"{term}:{i}") * 0.4
                        if score < threshold:
                            continue
                        conf = "high" if score >= 0.9 else ("medium" if score >= 0.75 else "low")
                        source = SOURCES_DISPLAY[i % len(SOURCES_DISPLAY)]
                        all_results.append(MatchResult(
                            code=f"C{int(100000 + deterministic_hash(f'{term}:cid:{i}') * 900000)}",
                            term=f'{source} concept for "{term}"',
                            definition=f"Simulated definition for {term}",
                            score=round(score, 3),
                            source="mock",
                        ))

            # Filter by threshold
            all_results = [r for r in all_results if r.score >= threshold]
            all_results.sort(key=lambda r: r.score, reverse=True)
            st.session_state["_sm_results"] = all_results

        # Display results
        if "_sm_results" in st.session_state and st.session_state["_sm_results"]:
            results = st.session_state["_sm_results"]
            st.markdown(f"##### Results ({len(results)})")

            ec, cc = st.columns([1, 1])
            with ec:
                df = pd.DataFrame([
                    {"Code": r.code, "Term": r.term, "Score": r.score, "Source": r.source,
                     "Definition": r.definition[:80]}
                    for r in results
                ])
                st.download_button("📥 Export CSV", df.to_csv(index=False), "mapping_results.csv", "text/csv")
            with cc:
                if st.button("✕ Clear"):
                    st.session_state["_sm_results"] = []
                    st.rerun()

            for r in results:
                render_match_result(r)

    with side_col:
        if "_sm_results" in st.session_state and st.session_state["_sm_results"]:
            results = st.session_state["_sm_results"]
            avg_score = sum(r.score for r in results) / len(results)
            st.markdown("##### Summary")
            st.markdown(f"**Total mappings:** {len(results)}")
            st.markdown(f"**Avg score:** {avg_score:.3f}")
            st.markdown(f"**Sources:** {', '.join(set(r.source for r in results))}")

        # Synonyms quick-lookup
        st.markdown("##### Quick Synonym Lookup")
        syn_input = st.text_input("Term or code", key="syn_input", placeholder="e.g. prostate or C7378")
        if syn_input.strip():
            if syn_input.strip().upper().startswith("C") and syn_input.strip()[1:].isdigit():
                syns = client.synonyms_by_code(syn_input.strip())
            else:
                syns = client.synonyms_by_term(syn_input.strip())
            if syns:
                for s in syns:
                    st.markdown(f"- {s}")
            else:
                st.caption("No synonyms found" + (" (Neo4j offline)" if not is_live else ""))

        st.markdown("##### Tips")
        st.markdown("- Enter one term per line\n- Auto mode tries exact → fuzzy → semantic\n- Use code format (C12345) for direct lookups")


# ═════════════════════════════════════════════
# PAGE: Graph Visualization — WIRED TO NEO4J
# ═════════════════════════════════════════════
def page_graph():
    st.markdown("## Graph Visualization")
    st.caption("Interactive knowledge graph explorer.")

    is_live = client.connected

    main_col, side_col = st.columns([3, 1])

    with side_col:
        if is_live:
            st.success("Live Neo4j graph", icon="🔗")
            center_term = st.text_input("Center node (term)", placeholder="e.g. Lung Carcinoma")
            limit = st.slider("Max nodes", 10, 200, 50, step=10)
        else:
            st.warning("Mock graph (Neo4j offline)")
            center_term = ""
            limit = 50

        layout_type = st.selectbox("Layout", ["Force-directed", "Circular", "Hierarchical", "Random"])
        search_term = st.text_input("🔍 Search nodes")

        with st.expander("Cypher Query Builder"):
            cypher = st.text_area("Query", "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 25", height=100)
            if is_live and st.button("▶ Run Cypher"):
                raw = client.run_cypher(cypher)
                if raw:
                    st.json(raw[:10])
                else:
                    st.info("No results")

    with main_col:
        # ── Fetch graph data ──
        if is_live:
            with st.spinner("Loading graph from Neo4j..."):
                payload = client.fetch_graph_neighbourhood(center_term=center_term or "", limit=limit)
            nodes = payload.nodes
            edges = payload.edges
            if not nodes:
                st.info("No nodes returned. Try a different center term or increase the limit.")
        else:
            nodes, edges = _generate_mock_graph(limit, layout_type)

        if not nodes:
            return

        # ── Compute positions ──
        positions = _compute_positions(nodes, layout_type)

        # ── Build Plotly figure ──
        fig = go.Figure()

        # Edges
        edge_x, edge_y = [], []
        name_to_pos = {n["name"]: positions.get(n["name"], (0, 0)) for n in nodes}
        for e in edges:
            if e["source"] in name_to_pos and e["target"] in name_to_pos:
                x0, y0 = name_to_pos[e["source"]]
                x1, y1 = name_to_pos[e["target"]]
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines",
                                  line=dict(width=1, color="rgba(180,180,180,0.25)"),
                                  hoverinfo="none", showlegend=False))

        # Nodes
        node_x = [positions[n["name"]][0] for n in nodes]
        node_y = [positions[n["name"]][1] for n in nodes]
        node_colors = [n.get("color", "#607d8b") for n in nodes]
        node_names = [n["name"] for n in nodes]
        node_hover = [f'{n["name"]} ({n.get("type","")})' for n in nodes]

        highlighted = [n["name"] for n in nodes if search_term and search_term.lower() in n["name"].lower()] if search_term else []
        marker_sizes = [18 if n["name"] in highlighted else 12 for n in nodes]

        fig.add_trace(go.Scatter(
            x=node_x, y=node_y, mode="markers+text", text=node_names,
            textposition="top center", hovertext=node_hover, hoverinfo="text",
            marker=dict(size=marker_sizes, color=node_colors,
                        line=dict(width=[3 if n["name"] in highlighted else 1 for n in nodes],
                                  color=["#22d3ee" if n["name"] in highlighted else "#fff" for n in nodes])),
            textfont=dict(size=8, color="#374151"), showlegend=False,
        ))

        fig.update_layout(
            height=600, showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="closest",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Legend
        type_colors = {}
        for n in nodes:
            t = n.get("type", "Unknown")
            if t not in type_colors:
                type_colors[t] = n.get("color", "#607d8b")
        legend_cols = st.columns(min(len(type_colors), 6))
        for i, (tp, col) in enumerate(type_colors.items()):
            with legend_cols[i % len(legend_cols)]:
                st.markdown(f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{col};margin-right:4px;"></span> {tp}', unsafe_allow_html=True)

        if search_term and highlighted:
            st.info(f"Found **{len(highlighted)}** matching nodes: {', '.join(highlighted[:8])}")


def _generate_mock_graph(n, layout):
    """Generate mock graph data (same as original)."""
    type_colors = {"Person": "#4fc3f7", "Document": "#4caf50", "Concept": "#ff9800", "Organization": "#9c27b0"}
    types = list(type_colors.keys())
    np.random.seed(42)
    nodes = [{"name": f"{types[i % 4]}_{i+1}", "type": types[i % 4], "color": type_colors[types[i % 4]]} for i in range(min(n, 50))]
    edges = []
    for i in range(len(nodes)):
        for _ in range(min(3, np.random.randint(1, 4))):
            j = np.random.randint(0, len(nodes))
            if i != j:
                src, tgt = nodes[i]["name"], nodes[j]["name"]
                if not any((e["source"] == src and e["target"] == tgt) for e in edges):
                    edges.append({"source": src, "target": tgt, "similarity": np.random.random()})
    return nodes, edges


def _compute_positions(nodes, layout_type):
    """Compute 2D positions for a list of node dicts."""
    positions = {}
    n = len(nodes)
    if layout_type == "Circular":
        for i, nd in enumerate(nodes):
            angle = 2 * math.pi * i / max(n, 1)
            positions[nd["name"]] = (math.cos(angle), math.sin(angle))
    elif layout_type == "Hierarchical":
        levels = 4
        per_level = max(1, n // levels)
        for i, nd in enumerate(nodes):
            lv = i // per_level
            pos = i % per_level
            positions[nd["name"]] = ((pos * 2.0) / max(per_level, 1) - 1, 1 - (lv * 2.0) / levels)
    elif layout_type == "Force-directed":
        np.random.seed(hash(str(len(nodes))) % 2**31)
        for nd in nodes:
            positions[nd["name"]] = ((np.random.random() - 0.5) * 4, (np.random.random() - 0.5) * 4)
        for _ in range(8):
            names = list(positions.keys())
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    a = list(positions[names[i]])
                    b = list(positions[names[j]])
                    dx, dy = a[0] - b[0], a[1] - b[1]
                    dist = math.sqrt(dx * dx + dy * dy) + 0.01
                    if dist < 1:
                        force = (1 - dist) * 0.05
                        a[0] += (dx / dist) * force; a[1] += (dy / dist) * force
                        b[0] -= (dx / dist) * force; b[1] -= (dy / dist) * force
                    positions[names[i]] = tuple(a)
                    positions[names[j]] = tuple(b)
    else:
        np.random.seed(42)
        for nd in nodes:
            positions[nd["name"]] = ((np.random.random() - 0.5) * 3, (np.random.random() - 0.5) * 3)
    return positions


# ═════════════════════════════════════════════
# PAGE: Dashboard (unchanged — all mock KPIs)
# ═════════════════════════════════════════════
def page_dashboard():
    st.markdown("## Frederick Dashboard")
    st.caption("Overview of system performance and activity.")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Total Queries", "45,392", "+15.3%", "up", "Total queries processed this month")
    with c2: metric_card("Graph Nodes", "8,247", "+523", "up", "Total nodes in knowledge graph")
    with c3: metric_card("Accuracy", "94.2%", "+2.1%", "up", "Model accuracy score")
    with c4: metric_card("Response Time", "0.34s", "-0.08s", "down", "Average response time")

    col_chart, col_pie = st.columns([2, 1])
    with col_chart:
        st.markdown("##### Query Volume")
        dates = [(datetime(2025, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
        queries = [1200 + (i * 37 % 800) + i * 10 for i in range(30)]
        successful = [1100 + (i * 29 % 800) + i * 9 for i in range(30)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=queries, name="Total Queries", line=dict(color="#374151", width=2)))
        fig.add_trace(go.Scatter(x=dates, y=successful, name="Successful", line=dict(color="#10b981", width=2)))
        fig.update_layout(height=320, margin=dict(l=40, r=20, t=20, b=40), legend=dict(orientation="h", y=-0.15), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with col_pie:
        st.markdown("##### Query Categories")
        fig_pie = go.Figure(data=[go.Pie(labels=["Search", "Analysis", "Visualization", "Export", "Other"], values=[35, 28, 20, 12, 5], hole=0.5, marker=dict(colors=["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#6b7280"]))])
        fig_pie.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("##### Recent Activity")
    for t, user, action, status in [("10:00 AM","Alice Chen","Uploaded dataset","success"),("10:30 AM","Bob Smith","Ran analysis","success"),("11:00 AM","Carol Davis","Created visualization","warning"),("11:30 AM","David Lee","Exported report","success"),("12:00 PM","Emma Wilson","Updated model","success")]:
        badge = f'<span class="badge-{status}">{status.capitalize()}</span>'
        st.markdown(f'<div class="activity-row"><div class="left"><span style="font-size:0.75rem;color:#94a3b8;width:4rem;">{t}</span><span style="font-size:0.85rem;font-weight:500;color:#0f172a;width:7rem;">{user}</span><span style="font-size:0.85rem;color:#64748b;">{action}</span></div>{badge}</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════
# PAGE: File Upload (unchanged)
# ═════════════════════════════════════════════
def page_file_upload():
    st.markdown("## Upload Files")
    st.caption("Upload training data, validation sets, or knowledge base files.")
    main_col, side_col = st.columns([2, 1])
    with main_col:
        upload_type = st.radio("Data type", ["Training", "Validation", "Test", "Knowledge Base"], horizontal=True)
        target_model = st.radio("Target model", ["RAG Model v2.0", "Classification v1.5", "NER v3.0", "Custom"], horizontal=True)
        st.markdown("---")
        uploaded_files = st.file_uploader("Drop files or click to browse", type=["pdf","txt","csv","json","doc","docx","xlsx"], accept_multiple_files=True)
        if uploaded_files:
            total_size = sum(f.size for f in uploaded_files)
            st.markdown(f"**{len(uploaded_files)} file(s)** · {total_size/1024:.1f} KB")
            for f in uploaded_files:
                st.markdown(f"📄 **{f.name}** — {f.size/1024:.1f} KB")
            if st.button("📤 Upload", type="primary"):
                progress = st.progress(0)
                for i in range(100):
                    time.sleep(0.02)
                    progress.progress(i + 1)
                st.success(f"✅ {len(uploaded_files)} file(s) uploaded!")
    with side_col:
        st.markdown("##### Recent Jobs")
        for jid, model, files, status, date in [("TRN-0846","RAG Model v2.0",12,"completed","Jan 20"),("TRN-0845","Classification v1.5",8,"running","Jan 19"),("TRN-0844","NER v3.0",15,"completed","Jan 18"),("TRN-0843","RAG Model v1.9",10,"failed","Jan 17")]:
            badge = f'<span class="badge-{status}">{status.capitalize()}</span>'
            st.markdown(f'<div style="background:#f8fafc;border-radius:0.75rem;padding:0.75rem;margin-bottom:0.35rem;"><div style="display:flex;justify-content:space-between;align-items:center;"><span style="font-size:0.85rem;font-weight:500;">{model}</span>{badge}</div><span style="font-size:0.7rem;color:#94a3b8;">{jid} · {files} files · {date}</span></div>', unsafe_allow_html=True)
        st.markdown("##### Tips")
        st.markdown("- Use CSV for structured term lists\n- JSON supports nested relationships\n- Max file size: 50MB per file")


# ═════════════════════════════════════════════
# PAGE: Feedback Portal (unchanged)
# ═════════════════════════════════════════════
def page_feedback():
    st.markdown("## Submit Feedback")
    st.caption("Report issues or suggest improvements to terminology mappings.")
    if "feedback_sent" not in st.session_state:
        st.session_state.feedback_sent = False
    if st.session_state.feedback_sent:
        st.success(f"✅ **Submitted!** Reference: FB-{np.random.randint(100,999)}")
        if st.button("Submit another"):
            st.session_state.feedback_sent = False
            st.rerun()
        return
    main_col, side_col = st.columns([2, 1])
    with main_col:
        with st.form("feedback_form"):
            c1, c2 = st.columns(2)
            with c1: name = st.text_input("Name")
            with c2: email = st.text_input("Email")
            issue_type = st.selectbox("Issue type", ["Incorrect mapping","Missing term","Suggestion","Relationship","Platform","Other"])
            priority = st.select_slider("Priority", options=["low","medium","high","critical"], value="medium")
            subject = st.text_input("Subject")
            c3, c4 = st.columns(2)
            with c3: term_ref = st.text_input("Term reference (optional)")
            with c4: concept_id = st.text_input("Concept ID (optional)")
            description = st.text_area("Description", height=120)
            cc = len(description.strip())
            st.caption(f"{'✅ ' if cc>=30 else ''}{cc}/30 characters")
            st.file_uploader("Attach files", accept_multiple_files=True, key="fb_files")
            if st.form_submit_button("Submit →", type="primary"):
                errors = []
                if not name.strip(): errors.append("Name required")
                if not email.strip() or "@" not in email: errors.append("Valid email required")
                if not subject.strip(): errors.append("Subject required")
                if cc < 30: errors.append("Description ≥ 30 chars")
                if errors:
                    for e in errors: st.error(e)
                else:
                    st.session_state.feedback_sent = True
                    st.rerun()
    with side_col:
        st.markdown("##### Recent Submissions")
        for fid, subj, status, date in [("FB-234","SNOMED mapping for atrial fibrillation","reviewing","Jan 19"),("FB-198","CAR-T cell therapy terminology","done","Jan 17"),("FB-156","HTN synonym for Hypertension","done","Jan 15"),("FB-142","Drug interaction hierarchy error","pending","Jan 12")]:
            lbl = {"reviewing":"In Review","done":"Resolved","pending":"Pending"}[status]
            st.markdown(f'<div style="background:#f8fafc;border-radius:0.75rem;padding:0.75rem;margin-bottom:0.35rem;"><div style="display:flex;justify-content:space-between;"><span style="font-size:0.85rem;font-weight:500;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{subj}</span><span class="badge-{status}">{lbl}</span></div><span style="font-size:0.7rem;color:#94a3b8;">{fid} · {date}</span></div>', unsafe_allow_html=True)
        st.markdown("##### Tips")
        st.markdown("- Include concept IDs when possible\n- Be specific about expected behavior\n- Attach screenshots for complex issues")


# ═════════════════════════════════════════════
# PAGE: Performance Metrics (unchanged)
# ═════════════════════════════════════════════
def page_results_analysis():
    st.markdown("## Performance Metrics")
    st.caption("Monitor system performance, usage, and resource utilization.")
    dc1, dc2, dc3, dc4 = st.columns([2, 2, 1, 1])
    with dc1: start_date = st.date_input("Start", datetime.now() - timedelta(days=30))
    with dc2: end_date = st.date_input("End", datetime.now())
    with dc3:
        if st.button("🔄 Refresh", type="primary"): st.rerun()
    with dc4:
        if st.button("📥 Export"): st.toast("Export initiated...")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Avg Response Time", "0.34s", "-12%", "down")
    with c2: metric_card("Success Rate", "94.2%", "+2.1%", "up")
    with c3: metric_card("Active Sessions", "127", "+15", "up")
    with c4: metric_card("Error Rate", "0.8%", "-0.3%", "down")
    tab_perf, tab_usage, tab_errors, tab_resources = st.tabs(["📊 Performance", "📈 Usage", "⚠️ Errors", "🖥️ Resources"])
    with tab_perf:
        pc1, pc2 = st.columns(2)
        with pc1:
            fig = go.Figure(data=[go.Histogram(x=np.exp(np.random.normal(0,0.5,1000)), nbinsx=30, marker_color="#4fc3f7")])
            fig.update_layout(height=300, margin=dict(l=50,r=30,t=20,b=50), xaxis_title="Response Time (s)", yaxis_title="Frequency", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        with pc2:
            hours = list(range(24))
            fig = go.Figure(data=[go.Bar(x=hours, y=[800+np.random.randint(0,400)+h*10 for h in hours], marker_color="#4caf50")])
            fig.update_layout(height=300, margin=dict(l=50,r=30,t=20,b=50), xaxis_title="Hour", yaxis_title="Requests/Hour", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    with tab_usage:
        st.dataframe(pd.DataFrame([{"Endpoint":"/search","Calls":"15,234","Avg (ms)":234,"Success":"99.2%"},{"Endpoint":"/analyze","Calls":"8,921","Avg (ms)":567,"Success":"97.8%"},{"Endpoint":"/graph","Calls":"6,547","Avg (ms)":890,"Success":"95.3%"},{"Endpoint":"/upload","Calls":"3,210","Avg (ms)":123,"Success":"99.9%"},{"Endpoint":"/export","Calls":"1,876","Avg (ms)":456,"Success":"98.1%"}]), use_container_width=True, hide_index=True)
    with tab_errors:
        ec1, ec2 = st.columns([2,1])
        with ec1:
            st.dataframe(pd.DataFrame([{"Type":"Timeout","Count":45,"Pct":"16.7%"},{"Type":"Bad Request","Count":123,"Pct":"45.6%"},{"Type":"Server Error","Count":12,"Pct":"4.4%"},{"Type":"Not Found","Count":67,"Pct":"24.8%"},{"Type":"Auth Failed","Count":23,"Pct":"8.5%"}]), use_container_width=True, hide_index=True)
        with ec2:
            fig = go.Figure(data=[go.Pie(labels=["Timeout","Bad Request","Server Error","Not Found","Auth Failed"], values=[45,123,12,67,23], hole=0.4)])
            fig.update_layout(height=250, margin=dict(l=20,r=20,t=20,b=20), paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    with tab_resources:
        rc1, rc2 = st.columns(2)
        with rc1:
            fig = go.Figure(data=[go.Scatter(y=[40+np.random.randint(0,40) for _ in range(60)], mode="lines", line=dict(color="#ff9800"))])
            fig.update_layout(title="CPU Usage (%)", height=250, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with rc2:
            fig = go.Figure(data=[go.Scatter(y=[50+np.random.randint(0,20) for _ in range(60)], mode="lines", line=dict(color="#9c27b0"))])
            fig.update_layout(title="Memory Usage (%)", height=250, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)


# ═════════════════════════════════════════════
# PAGE: Settings
# ═════════════════════════════════════════════
def page_settings():
    st.markdown("## Settings")
    st.caption("Configure your application preferences and settings.")
    settings = st.session_state.settings

    st.markdown("##### 🔌 Backend Connection")
    st.code(f"NEO4J_URI = {client.neo4j_uri or '(not set)'}\nNEO4J_USERNAME = {client.neo4j_user or '(not set)'}", language="text")
    status = client.status_dict()
    for k, v in status.items():
        st.markdown(f"**{k}:** {'✅' if v is True else ('❌' if v is False else (v or '—'))}")

    st.markdown("---")

    # ── System Prompt Editor (Sprint 11) ──
    st.markdown("##### 🧠 System Prompt")
    st.caption("This prompt is used by the AI chat agent and the NL-to-Cypher query engine. Changes apply globally.")
    sys_prompt = st.text_area(
        "System Prompt",
        value=st.session_state.system_prompt,
        height=180,
        key="settings_system_prompt",
    )
    sp_c1, sp_c2, sp_c3 = st.columns([1, 1, 4])
    with sp_c1:
        if st.button("💾 Save Prompt", key="settings_save_prompt"):
            st.session_state.system_prompt = sys_prompt
            st.success("System prompt saved!")
    with sp_c2:
        if st.button("↩️ Reset to Default", key="settings_reset_prompt"):
            st.session_state.system_prompt = (
                "You are an expert medical data mapper specializing in NCIT (National Cancer Institute Thesaurus) terminology.\n"
                "Your job is to help map raw medical data values to standardized NCIT terms and codes.\n"
                "Be thorough but concise in your analysis. Always provide the recommended NCIT code and term if found."
            )
            st.rerun()

    st.markdown("---")
    st.markdown("##### 🌓 Theme")
    settings["dark_mode"] = st.toggle("Dark Mode", value=settings["dark_mode"])
    st.markdown("##### 🔔 Notifications")
    settings["notifications"] = st.toggle("Notifications", value=settings["notifications"])
    st.markdown("##### 🖥️ API Endpoint")
    settings["api_endpoint"] = st.text_input("API Endpoint", value=settings["api_endpoint"])

    if st.button("💾 Save Settings", type="primary"):
        st.session_state.settings = settings
        st.success("Settings saved!")


# ═════════════════════════════════════════════
# PAGE: SME Workbench (Sprint 11 — NEW)
#   Pat's workflow: upload terms → see ranked synonyms → grade them
# ═════════════════════════════════════════════
def page_sme_workbench():
    st.markdown("## 🧪 SME Workbench")
    st.caption("Upload a list of data terms. The system finds the closest matches in the caDSR/NCIT database. You can then review and grade each match.")

    is_live = client.connected

    if is_live:
        st.success("🔗 Connected to live Neo4j — results are real", icon="✅")
    else:
        st.warning("⚠️ Neo4j offline — showing mock results for demonstration")

    # ── System Prompt (affects how the agent searches) ──
    with st.expander("⚙️ System Prompt / Search Configuration", expanded=False):
        st.caption("Optional: Adjust the system prompt that guides how terms are matched.")
        sme_prompt = st.text_area(
            "System Prompt",
            value=st.session_state.system_prompt,
            height=100,
            key="sme_system_prompt",
        )
        if st.button("💾 Update", key="sme_save_prompt"):
            st.session_state.system_prompt = sme_prompt
            st.success("Prompt updated!")

    st.markdown("---")

    # ── Input: File upload OR manual entry ──
    input_mode = st.radio("Input mode", ["📄 Upload file", "⌨️ Type terms manually"], horizontal=True)

    top_k = st.slider("Top K matches per term", 3, 20, 10, help="How many candidate synonyms to return for each input term")

    terms = []

    if input_mode == "📄 Upload file":
        uploaded = st.file_uploader(
            "Upload your terms file (.txt, .csv, or .tsv)",
            type=["txt", "csv", "tsv"],
            help="One term per line, comma-separated, or tab-delimited. The first column is treated as the term."
        )
        if uploaded:
            content = uploaded.read().decode("utf-8", errors="replace")
            # Parse the file (same logic as backend)
            raw_terms = []
            if "\t" in content:
                for line in content.strip().splitlines():
                    parts = line.split("\t")
                    t = parts[0].strip()
                    if t and not t.lower().startswith("term") and not t.startswith("#"):
                        raw_terms.append(t)
            elif "," in content.splitlines()[0] if content.strip() else False:
                for line in content.strip().splitlines():
                    if line.startswith("#"):
                        continue
                    for part in line.split(","):
                        t = part.strip()
                        if t and t.lower() not in ("term", "terms", "category", "definition"):
                            raw_terms.append(t)
            else:
                for line in content.strip().splitlines():
                    t = line.strip()
                    if t and not t.startswith("#"):
                        raw_terms.append(t)
            # Deduplicate
            seen = set()
            for t in raw_terms:
                if t.lower() not in seen:
                    seen.add(t.lower())
                    terms.append(t)
            st.info(f"📋 Parsed **{len(terms)}** unique terms from `{uploaded.name}`")
            if terms:
                with st.expander("Preview parsed terms"):
                    st.write(terms)
    else:
        manual_input = st.text_area("Enter terms (one per line or comma-separated)", placeholder="glucose\nhemoglobin\ninsulin\nalbumin", height=120)
        if manual_input.strip():
            if "," in manual_input:
                terms = [t.strip() for t in manual_input.split(",") if t.strip()]
            else:
                terms = [t.strip() for t in manual_input.strip().splitlines() if t.strip()]

    # ── Run search ──
    run = st.button("🔎 Find Matches", type="primary", disabled=not terms)

    if run and terms:
        all_results = {}
        progress = st.progress(0, text="Searching...")
        for i, term in enumerate(terms):
            progress.progress((i + 1) / len(terms), text=f"Searching: {term}")

            if is_live:
                # Use the backend client's cascade: exact → fuzzy → synonym path
                matches = []
                # Exact
                exact = client.exact_match_by_term(term)
                if exact:
                    matches.append({
                        "rank": 1, "code": exact.code, "term": exact.term,
                        "definition": exact.definition, "type": exact.node_type,
                        "match_method": "exact", "score": 1.0,
                    })
                # Fuzzy
                fuzzy = client.fuzzy_match(term, limit=top_k)
                for f in fuzzy:
                    if not any(m["code"] == f.code for m in matches):
                        matches.append({
                            "rank": len(matches) + 1, "code": f.code, "term": f.term,
                            "definition": f.definition, "type": f.node_type,
                            "match_method": "fuzzy", "score": f.score,
                        })
                # Synonym path
                syns = client.synonyms_by_term(term)
                for s in syns[:top_k]:
                    if not any(m["term"] == s for m in matches):
                        matches.append({
                            "rank": len(matches) + 1, "code": "", "term": s,
                            "definition": "", "type": "SYN",
                            "match_method": "synonym_path", "score": 0.7,
                        })
                # Re-rank
                matches.sort(key=lambda x: x["score"], reverse=True)
                for idx, m in enumerate(matches):
                    m["rank"] = idx + 1
                all_results[term] = matches[:top_k]
            else:
                # Mock
                all_results[term] = [
                    {
                        "rank": j + 1,
                        "code": f"C{10000 + abs(hash(term + str(j))) % 90000}",
                        "term": f"Mock match {j+1} for {term}",
                        "definition": f"Simulated definition for a match of '{term}'.",
                        "type": "NCIT", "match_method": "mock",
                        "score": round(0.95 - j * 0.08, 3),
                    }
                    for j in range(min(top_k, 5))
                ]
        progress.empty()
        st.session_state.sme_results = all_results

    # ── Display results with grading UI ──
    if st.session_state.sme_results:
        results = st.session_state.sme_results
        st.markdown("---")
        st.markdown(f"### Results ({len(results)} terms)")

        # Export all results as CSV
        export_rows = []
        for input_term, matches in results.items():
            for m in matches:
                export_rows.append({
                    "Input Term": input_term,
                    "Rank": m["rank"],
                    "Code": m["code"],
                    "Matched Term": m["term"],
                    "Definition": m["definition"],
                    "Type": m["type"],
                    "Method": m["match_method"],
                    "Score": m["score"],
                    "SME Grade": st.session_state.sme_grades.get(f"{input_term}|{m['code']}|{m['term']}", ""),
                })
        export_df = pd.DataFrame(export_rows)
        st.download_button("📥 Export all results as CSV", export_df.to_csv(index=False), "sme_workbench_results.csv", "text/csv")

        # Per-term accordion with grading table
        for input_term, matches in results.items():
            with st.expander(f"🔬 **{input_term}** — {len(matches)} matches", expanded=True):
                if not matches:
                    st.caption("No matches found.")
                    continue

                # Build an editable dataframe for this term
                rows = []
                for m in matches:
                    grade_key = f"{input_term}|{m['code']}|{m['term']}"
                    rows.append({
                        "Rank": m["rank"],
                        "Code": m["code"],
                        "Term": m["term"],
                        "Definition": m["definition"][:100] + ("..." if len(m["definition"]) > 100 else ""),
                        "Method": m["match_method"],
                        "Score": m["score"],
                        "Grade": st.session_state.sme_grades.get(grade_key, "—"),
                })

                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Grading controls
                st.caption("**Grade the best match:**")
                grade_cols = st.columns(min(len(matches), 5))
                for j, m in enumerate(matches[:5]):
                    with grade_cols[j % 5]:
                        grade_key = f"{input_term}|{m['code']}|{m['term']}"
                        current = st.session_state.sme_grades.get(grade_key, "—")
                        label = f"#{m['rank']} {m['term'][:20]}"
                        grade = st.selectbox(
                            label,
                            ["—", "✅ Accept", "🤔 Maybe", "❌ Reject"],
                            index=["—", "✅ Accept", "🤔 Maybe", "❌ Reject"].index(current) if current in ["—", "✅ Accept", "🤔 Maybe", "❌ Reject"] else 0,
                            key=f"grade_{grade_key}",
                        )
                        if grade != "—":
                            st.session_state.sme_grades[grade_key] = grade

        # Summary of grades
        if st.session_state.sme_grades:
            st.markdown("---")
            st.markdown("### 📊 Grading Summary")
            grade_counts = {"✅ Accept": 0, "🤔 Maybe": 0, "❌ Reject": 0}
            for g in st.session_state.sme_grades.values():
                if g in grade_counts:
                    grade_counts[g] += 1
            gc1, gc2, gc3 = st.columns(3)
            with gc1:
                st.metric("Accepted", grade_counts["✅ Accept"])
            with gc2:
                st.metric("Maybe", grade_counts["🤔 Maybe"])
            with gc3:
                st.metric("Rejected", grade_counts["❌ Reject"])


# ═════════════════════════════════════════════
# PAGE: Graph Query (Sprint 11 — NEW)
#   Natural language → Ollama → Cypher → Neo4j results
# ═════════════════════════════════════════════
def page_graph_query():
    st.markdown("## 🔍 Graph Query (Natural Language)")
    st.caption("Ask questions about the knowledge graph in plain English. The system uses Ollama to convert your question into a Cypher query and runs it against Neo4j.")

    is_live = client.connected

    # ── Status badges ──
    status_cols = st.columns(3)
    with status_cols[0]:
        if is_live:
            st.success("Neo4j: Connected", icon="✅")
        else:
            st.error("Neo4j: Offline", icon="❌")
    with status_cols[1]:
        # Probe Ollama on first visit
        ollama_ok = client.ollama_ready
        if ollama_ok:
            st.success("Ollama: Connected", icon="🤖")
        else:
            st.warning("Ollama: Offline (using pattern fallback)", icon="⚠️")
    with status_cols[2]:
        st.info("Queries generated & executed live", icon="🔍")

    # ── System Prompt (editable) ──
    with st.expander("⚙️ NL-to-Cypher System Prompt", expanded=False):
        st.caption(
            "This prompt is sent to Ollama before your question. "
            "It teaches the LLM the graph schema and how to write Cypher. "
            "Edit it to change behaviour or add domain-specific hints."
        )
        nl_prompt = st.text_area(
            "Prompt",
            value=st.session_state.get("_nl_prompt", client.GRAPH_SCHEMA_PROMPT),
            height=200,
            key="nl_cypher_prompt",
        )
        prc1, prc2 = st.columns([1, 5])
        with prc1:
            if st.button("💾 Save", key="save_nl_prompt"):
                st.session_state["_nl_prompt"] = nl_prompt
                st.success("Prompt saved for this session!")
        with prc2:
            if st.button("↩️ Reset", key="reset_nl_prompt"):
                st.session_state["_nl_prompt"] = client.GRAPH_SCHEMA_PROMPT
                st.rerun()

    st.markdown("---")

    # ── Example questions ──
    st.markdown("**Try these examples:**")
    examples = [
        "How many synonyms are there for C1234?",
        "Show me all synonyms for 'Lung Carcinoma'",
        "What CDEs use the concept C4878?",
        "Find permissible values related to prostate",
        "List NCIT concepts with 'diabetes' in the name",
    ]
    ex_cols = st.columns(len(examples))
    for i, ex in enumerate(examples):
        with ex_cols[i]:
            if st.button(f"💡 {ex[:30]}...", key=f"ex_{i}", use_container_width=True):
                st.session_state["_gq_question"] = ex
                st.rerun()

    # ── Question input ──
    question = st.text_input(
        "Your question",
        value=st.session_state.get("_gq_question", ""),
        placeholder="e.g. How many synonyms are there for C1234?",
        key="graph_query_input",
    )

    run_query = st.button("🚀 Run Query", type="primary", disabled=not question.strip())

    if run_query and question.strip():
        with st.spinner("Generating Cypher via Ollama and querying Neo4j..."):
            prompt_to_use = st.session_state.get("_nl_prompt", None)
            result = client.nl_to_cypher(question, system_prompt=prompt_to_use)

        # Store in history
        st.session_state.graph_query_history.insert(0, result)
        # Clear the prefilled question
        if "_gq_question" in st.session_state:
            del st.session_state["_gq_question"]

    # ── Display latest result ──
    if st.session_state.graph_query_history:
        latest = st.session_state.graph_query_history[0]

        st.markdown("---")

        # Method badge
        if latest["method"] == "ollama":
            st.success("🤖 Cypher generated by **Ollama LLM**")
        else:
            st.info("🔧 Cypher generated by **pattern-based fallback** (Ollama unavailable)")

        st.markdown("##### Generated Cypher Query")
        st.code(latest["cypher"], language="cypher")

        if latest.get("error"):
            st.warning(f"⚠️ {latest['error']}")

        if latest["results"]:
            st.markdown(f"##### Results ({latest['total']} rows)")
            df = pd.DataFrame(latest["results"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("📥 Export CSV", df.to_csv(index=False), "graph_query_results.csv", "text/csv")
        elif not latest.get("error"):
            st.info("No results returned.")

        # ── Manual edit & re-run ──
        with st.expander("✏️ Edit & re-run Cypher manually"):
            edited = st.text_area("Cypher", value=latest["cypher"], height=100, key="edit_cypher")
            if st.button("▶️ Execute edited query", key="rerun_edited"):
                with st.spinner("Running..."):
                    rows = client.run_cypher(edited)
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.info("No results (or Neo4j offline)")

    # ── Query history ──
    if len(st.session_state.graph_query_history) > 1:
        with st.expander(f"📜 Query History ({len(st.session_state.graph_query_history)} queries)"):
            for i, h in enumerate(st.session_state.graph_query_history):
                method_icon = "🤖" if h["method"] == "ollama" else "🔧"
                st.markdown(f"**{i+1}.** {method_icon} {h['question']}")
                st.code(h["cypher"], language="cypher")
                if h["results"]:
                    st.caption(f"→ {h['total']} results")
                if h.get("error"):
                    st.caption(f"⚠️ {h['error']}")
                st.markdown("---")


# ──────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────
page = st.session_state.page
if page == "Home": page_home()
elif page == "Dashboard": page_dashboard()
elif page == "SME Workbench": page_sme_workbench()
elif page == "Graph Query": page_graph_query()
elif page == "Semantic Mapping": page_semantic_mapping()
elif page == "Graph Visualization": page_graph()
elif page == "File Upload": page_file_upload()
elif page == "Feedback Portal": page_feedback()
elif page == "Performance Metrics": page_results_analysis()
elif page == "Settings": page_settings()

st.markdown("---")
st.caption("Frederick Platform (Streamlit) v1.0.0 | Powered by RAG & Neo4j | © 2025 Frederick AI")
