"""Sidebar: backend status, model config, navigation."""

import streamlit as st
from app.services.neo4j_client import BackendClient


# Grouped navigation: primary workflows first, admin second
NAV_GROUPS = {
    "Workflows": {
        "Home": "🏠",
        "Map & Grade": "🎯",
        "Explore Graph": "🕸️",
    },
    "Admin": {
        "Dashboard": "📊",
        "Ingest Data": "📤",
        "Settings": "⚙️",
    },
}


def render_sidebar(client: BackendClient):
    """Render the full sidebar and return the selected page name."""
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

        st.markdown("---")

        # ── Model configuration ──
        st.markdown("**🧠 Model Configuration**")
        agent_model = st.text_input(
            "Reasoning Model (Agent)",
            value=st.session_state.get("agent_model", "llama3.1"),
            help="e.g., qwen2.5, llama3.1-64",
        )
        cypher_model = st.text_input(
            "Cypher Gen Model (Fast)",
            value=st.session_state.get("cypher_model", "llama3.1"),
            help="Used for Natural Language to Cypher",
        )
        st.session_state["agent_model"] = agent_model
        st.session_state["cypher_model"] = cypher_model

        if st.button("🚀 Initialize / Swap Agent", use_container_width=True):
            with st.spinner(f"Loading {agent_model} into memory..."):
                ok = client.init_agent(model_name=agent_model)
                if ok:
                    st.success(f"Agent ready using {agent_model}!")
                else:
                    st.error(f"Agent failed: {client.error}")

        current_model = getattr(client, "current_agent_model", "unknown")
        agent_status = f"🟢 Ready ({current_model})" if status["agent_ready"] else "🔴 Not Initialized"
        st.write(f"Agent Status: **{agent_status}**")

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
