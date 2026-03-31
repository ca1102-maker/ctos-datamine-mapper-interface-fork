"""Home page — AI chat with Neo4j-persisted history + quick navigation."""

import streamlit as st
from app.services.neo4j_client import BackendClient


def page_home(client: BackendClient):
    st.markdown("## How can I help you today?")
    st.caption("Ask about semantic mappings, terminology, or explore our features.")

    # Load chat sessions from Neo4j
    st.session_state.chat_sessions = client.list_chat_sessions(limit=30)

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

    # ── Two-column layout: chat + history ──
    chat_col, history_col = st.columns([4, 1.35], gap="large")

    # ── RIGHT: Chat history panel ──
    with history_col:
        st.markdown("### 💬 Chat History")

        if st.button("➕ New Chat", key="new_chat_button", use_container_width=True):
            st.session_state.current_chat_id = None
            st.session_state.chat_messages = []
            st.rerun()

        st.markdown("---")

        if st.session_state.chat_sessions:
            for session in st.session_state.chat_sessions:
                chat_id = session.get("chat_id")
                title = session.get("title") or "Untitled Chat"
                is_current = st.session_state.current_chat_id == chat_id
                label = f"🟢 {title[:35]}" if is_current else f"💬 {title[:35]}"

                if st.button(
                    label,
                    key=f"chat_session_{chat_id}",
                    use_container_width=True,
                    type="primary" if is_current else "secondary",
                ):
                    loaded = client.load_chat_messages(chat_id)
                    st.session_state.current_chat_id = chat_id
                    st.session_state.chat_messages = [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in loaded
                    ]
                    st.rerun()
        else:
            st.caption("No previous chats yet.")

    # ── LEFT: Active chat ──
    with chat_col:
        # Display messages
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Suggested prompts (only when empty)
        if not st.session_state.chat_messages:
            suggested = [
                "Tell me more about semantic mapping in medical terminology",
                "Explain common terminology mapping approaches",
                "Help me understand Neo4j graph relationships",
            ]
            for prompt in suggested:
                if st.button(f"🔍  {prompt}", key=f"suggest_{prompt[:20]}", use_container_width=True):
                    _handle_user_message(client, prompt)
                    st.rerun()

        # Chat input
        if user_input := st.chat_input("Ask anything about your knowledge base"):
            _handle_user_message(client, user_input)
            st.rerun()


def _handle_user_message(client: BackendClient, user_input: str):
    """Create session if needed, save user message, get reply, save reply."""
    # Create new chat session if needed
    if st.session_state.current_chat_id is None:
        created = client.create_chat_session(title=user_input[:60])
        if created["ok"]:
            st.session_state.current_chat_id = created["chat_id"]

    user_position = len(st.session_state.chat_messages)

    # Save user message locally
    st.session_state.chat_messages.append({"role": "user", "content": user_input})

    # Save to Neo4j
    if st.session_state.current_chat_id:
        client.save_chat_message(
            chat_id=st.session_state.current_chat_id,
            role="user", content=user_input, position=user_position,
        )
        # Set title from first message
        if user_position == 0:
            client.update_chat_session_title(
                st.session_state.current_chat_id, user_input[:60]
            )

    # Generate reply using smart routing (Ollama → Claude → mock)
    reply = client.chat_query(user_input, system_prompt=st.session_state.system_prompt)

    assistant_position = len(st.session_state.chat_messages)

    # Save reply locally
    st.session_state.chat_messages.append({"role": "assistant", "content": reply})

    # Save to Neo4j
    if st.session_state.current_chat_id:
        client.save_chat_message(
            chat_id=st.session_state.current_chat_id,
            role="assistant", content=reply, position=assistant_position,
        )
