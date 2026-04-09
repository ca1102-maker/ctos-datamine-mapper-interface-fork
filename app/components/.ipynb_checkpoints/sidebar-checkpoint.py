"""Sidebar: backend status, model config with Ollama model discovery, navigation."""

import streamlit as st
import requests
from app.services.neo4j_client import BackendClient


NAV_GROUPS = {
    "Workflows": {
        "Home": "🏠",
        "Map & Grade": "🎯",
        "Explore Graph": "🕸️",
    },
    "Admin": {
        "Dashboard": "📊",
        "Ingest Data": "📤",
        "Benchmark": "🏆",
        "Settings": "⚙️",
    },
}

# Default fallback list if Ollama API is unreachable
FALLBACK_MODELS = ["llama3.1-64", "llama3.1", "qwen2.5", "mistral", "codellama"]


def _fetch_ollama_models() -> list[str]:
    """Query the Ollama API for locally installed models."""
    if "ollama_models" in st.session_state:
        return st.session_state["ollama_models"]
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        models.sort()
        st.session_state["ollama_models"] = models if models else FALLBACK_MODELS
    except Exception:
        st.session_state["ollama_models"] = FALLBACK_MODELS
    return st.session_state["ollama_models"]


def render_sidebar(client: BackendClient):
    """Render the full sidebar."""
    with st.sidebar:
        st.markdown("### 🧬 Frederick Platform")

        # ── Backend status ──
        status = client.status_dict()
        if status["neo4j_connected"]:
            st.success("Neo4j: Connected", icon="✅")
        else:
            st.error("Neo4j: Offline (mock data)", icon="❌")
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
        st.caption(f"Claude API: {'✅ Key set' if status.get('claude_ready') else '❌ No API key'}")

        st.markdown("---")

        # ── Model configuration ──
        st.markdown("**🧠 Model Configuration**")

        available_models = _fetch_ollama_models()

        # Agent model selector
        default_agent = st.session_state.get("agent_model", "llama3.1-64")
        agent_idx = available_models.index(default_agent) if default_agent in available_models else 0
        agent_model = st.selectbox(
            "Reasoning Model (Agent)",
            available_models,
            index=agent_idx,
            help="Select which locally installed Ollama model to use for the chat agent.",
        )

        # Cypher model selector
        default_cypher = st.session_state.get("cypher_model", "llama3.1-64")
        cypher_idx = available_models.index(default_cypher) if default_cypher in available_models else 0
        cypher_model = st.selectbox(
            "Cypher Gen Model (Fast)",
            available_models,
            index=cypher_idx,
            help="Select which model to use for Natural Language to Cypher generation.",
        )

        st.session_state["agent_model"] = agent_model
        st.session_state["cypher_model"] = cypher_model

        # Refresh model list button
        if st.button("🔄 Refresh models", use_container_width=True):
            if "ollama_models" in st.session_state:
                del st.session_state["ollama_models"]
            st.rerun()

        # Swap agent if model changed or not yet initialized
        current_model = getattr(client, "current_agent_model", None)
        if not status["agent_ready"] or current_model != agent_model:
            with st.spinner(f"Loading {agent_model}..."):
                client.init_agent(model_name=agent_model)

        if client.agent_ready:
            st.caption(f"Agent: 🟢 {client.current_agent_model}")
        else:
            st.caption(f"Agent: 🔴 Failed — using Claude/mock fallback")

        st.markdown("---")

        # ── Grouped navigation ──
        for group_name, pages in NAV_GROUPS.items():
            st.caption(group_name.upper())
            for page_name, icon in pages.items():
                is_active = st.session_state.page == page_name
                if st.button(
                    f"{icon}  {page_name}",
                    key=f"nav_{page_name}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state.page = page_name
                    st.rerun()
            st.markdown("")