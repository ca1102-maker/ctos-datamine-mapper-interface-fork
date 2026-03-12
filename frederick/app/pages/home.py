"""Home page — AI chat + quick navigation cards."""

import streamlit as st
from app.services.neo4j_client import BackendClient


def page_home(client: BackendClient):
    st.markdown("## 🏠 Frederick Platform")
    st.caption("AI-powered medical terminology mapping and knowledge graph exploration.")

    # ── System Prompt Editor ──
    with st.expander("⚙️ Edit System Prompt", expanded=False):
        st.caption("Customise how the AI agent responds.")
        new_prompt = st.text_area(
            "System Prompt",
            value=st.session_state.system_prompt,
            height=160,
            key="home_system_prompt_editor",
        )
        col_save, col_reset, _ = st.columns([1, 1, 4])
        with col_save:
            if st.button("💾 Save Prompt", key="save_prompt_home"):
                st.session_state.system_prompt = new_prompt
                st.success("System prompt updated!")
        with col_reset:
            if st.button("↩️ Reset", key="reset_prompt_home"):
                st.session_state.system_prompt = (
                    "You are an expert medical data mapper specializing in NCIT terminology.\n"
                    "Your job is to help map raw medical data values to standardized NCIT terms and codes.\n"
                    "Be thorough but concise in your analysis."
                )
                st.rerun()

    # ── Quick nav ──
    nav_items = [
        ("Map & Grade", "Upload terms and map to NCIT/caDSR with grading"),
        ("Explore Graph", "Query and visualize the knowledge graph"),
        ("Dashboard", "View metrics and system overview"),
        ("Ingest Data", "Upload EVS results into Neo4j"),
        ("Settings", "Connection info and preferences"),
    ]
    cols = st.columns(3)
    for i, (name, desc) in enumerate(nav_items):
        with cols[i % 3]:
            if st.button(f"**{name}**\n\n{desc}", key=f"home_nav_{name}", use_container_width=True):
                st.session_state.page = name
                st.rerun()

    st.markdown("---")

    # ── Chat ──
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
                f"*💡 Initialise the agent in the sidebar for live Neo4j-backed answers.*"
            )

        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        st.rerun()
