"""Settings — connection info, system prompt, preferences."""

import streamlit as st

from app.services.neo4j_client import BackendClient


def page_settings(client: BackendClient):
    st.markdown("## ⚙️ Settings")
    st.caption("Configure your application preferences and settings.")

    # ── Backend connection ──
    st.markdown("##### 🔌 Backend Connection")
    st.code(
        f"NEO4J_URI = {client.neo4j_uri or '(not set)'}\n"
        f"NEO4J_USERNAME = {client.neo4j_user or '(not set)'}",
        language="text",
    )
    status = client.status_dict()
    for k, v in status.items():
        st.markdown(f"**{k}:** {'✅' if v is True else ('❌' if v is False else (v or '—'))}")

    st.markdown("---")

    # ── System prompt ──
    st.markdown("##### 🧠 System Prompt")
    st.caption("Used by the AI chat agent and the NL-to-Cypher engine.")
    sys_prompt = st.text_area(
        "System Prompt",
        value=st.session_state.system_prompt,
        height=180,
        key="settings_system_prompt",
    )
    sp1, sp2, _ = st.columns([1, 1, 4])
    with sp1:
        if st.button("💾 Save", key="settings_save_prompt"):
            st.session_state.system_prompt = sys_prompt
            st.success("System prompt saved!")
    with sp2:
        if st.button("↩️ Reset", key="settings_reset_prompt"):
            st.session_state.system_prompt = (
                "You are an expert medical data mapper specializing in NCIT terminology.\n"
                "Your job is to help map raw medical data values to standardized NCIT terms and codes.\n"
                "Be thorough but concise in your analysis."
            )
            st.rerun()

    st.markdown("---")

    # ── Preferences ──
    settings = st.session_state.settings
    st.markdown("##### 🌓 Theme")
    settings["dark_mode"] = st.toggle("Dark Mode", value=settings["dark_mode"])
    st.markdown("##### 🔔 Notifications")
    settings["notifications"] = st.toggle("Notifications", value=settings["notifications"])
    st.markdown("##### 🖥️ API Endpoint")
    settings["api_endpoint"] = st.text_input("API Endpoint", value=settings["api_endpoint"])

    if st.button("💾 Save Settings", type="primary"):
        st.session_state.settings = settings
        st.success("Settings saved!")
