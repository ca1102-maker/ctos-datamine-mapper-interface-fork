"""Sidebar: backend status, model config with OpenAI model selection, navigation."""

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

# Available OpenAI models
FALLBACK_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]


def _fetch_openai_models() -> list[str]:
    """Return available OpenAI models."""
    return FALLBACK_MODELS


def render_sidebar(client: BackendClient):
    """Render the full sidebar."""
    with st.sidebar:
        st.markdown("### 🧬 Frederick Platform")

        # ── Logged-in user ──
        display_name = st.session_state.get("logged_in_display_name", "")
        if display_name:
            st.markdown(f"👤 **{display_name}**")

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

        st.caption(f"OpenAI: {"✅ Ready" if status.get("openai_ready") else "⏳ Not tested yet"}")
        st.caption(f"Claude API: {'✅ Key set' if status.get('claude_ready') else '❌ No API key'}")

        st.markdown("---")

        # ── Model configuration ──
        st.markdown("**🧠 Model Configuration**")

        available_models = FALLBACK_MODELS

        # Agent model selector
        default_agent = st.session_state.get("agent_model", "llama3.1-64")
        agent_idx = available_models.index(default_agent) if default_agent in available_models else 0
        agent_model = st.selectbox(
            "Reasoning Model (Agent)",
            available_models,
            index=agent_idx,
            help="Select which OpenAI model to use for the chat agent.",
        )

        # Cypher model selector
        default_cypher = st.session_state.get("cypher_model", "llama3.1-64")
        cypher_idx = available_models.index(default_cypher) if default_cypher in available_models else 0
        cypher_model = st.selectbox(
            "Cypher Gen Model (Fast)",
            available_models,
            index=cypher_idx,
            help="Select which OpenAI model to use for Natural Language to Cypher generation.",
        )

        st.session_state["agent_model"] = agent_model
        st.session_state["cypher_model"] = cypher_model

        # Refresh model list button
        if st.button("🔄 Refresh models", use_container_width=True):
            pass
            st.rerun()

        # Swap agent if model changed or not yet initialized
        current_model = getattr(client, "current_agent_model", None)
        if not status["agent_ready"] or current_model != agent_model:
            with st.spinner(f"Loading {agent_model}..."):
                client.init_agent(model_name=agent_model)

        if client.agent_ready:
            st.caption(f"Agent: 🟢 {client.current_agent_model}")
        else:
            st.caption("Agent: 🔴 Failed — using Claude/mock fallback")

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
            st.markdown("")  # spacer between groups

        # ── Logout ──
        st.markdown("---")
        if st.button("🚪 Log Out", key="logout_btn", use_container_width=True):
            for key in [
                "logged_in_user_id", "logged_in_username", "logged_in_display_name",
                "current_chat_id", "chat_messages", "chat_sessions",
            ]:
                st.session_state.pop(key, None)
            st.rerun()
