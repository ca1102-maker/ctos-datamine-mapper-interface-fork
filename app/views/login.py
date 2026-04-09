"""Login / Sign-up page for the Frederick Platform."""

import streamlit as st
from app.services.neo4j_client import BackendClient


def page_login(client: BackendClient):
    """Render a centered login / create-account form."""

    # ── Centered container ──
    _spacer_l, col, _spacer_r = st.columns([1, 2, 1])

    with col:
        st.markdown(
            "<h1 style='text-align:center;'>🧬 Frederick Platform</h1>"
            "<p style='text-align:center; color:#64748b;'>"
            "Medical terminology mapping powered by Neo4j & LangChain"
            "</p>",
            unsafe_allow_html=True,
        )

        st.markdown("")  # spacer

        # Toggle between Login and Sign Up
        if "auth_mode" not in st.session_state:
            st.session_state.auth_mode = "login"

        login_tab, signup_tab = st.tabs(["🔑 Log In", "📝 Create Account"])

        # ── Log In ──
        with login_tab:
            with st.form("login_form", clear_on_submit=False):
                login_user = st.text_input("Username", key="login_username")
                login_pass = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Log In", use_container_width=True, type="primary")

                if submitted:
                    if not login_user or not login_pass:
                        st.error("Please enter both username and password.")
                    else:
                        result = client.authenticate_user(login_user, login_pass)
                        if result["ok"]:
                            st.session_state.logged_in_user_id = result["user_id"]
                            st.session_state.logged_in_username = login_user.strip().lower()
                            st.session_state.logged_in_display_name = result["display_name"]
                            st.rerun()
                        else:
                            st.error(result["error"])

        # ── Sign Up ──
        with signup_tab:
            with st.form("signup_form", clear_on_submit=False):
                new_user = st.text_input("Choose a username", key="signup_username")
                new_display = st.text_input("Display name (optional)", key="signup_display")
                new_pass = st.text_input("Password", type="password", key="signup_password")
                new_pass2 = st.text_input("Confirm password", type="password", key="signup_password2")
                created = st.form_submit_button("Create Account", use_container_width=True, type="primary")

                if created:
                    if not new_user or not new_pass:
                        st.error("Username and password are required.")
                    elif len(new_pass) < 4:
                        st.error("Password must be at least 4 characters.")
                    elif new_pass != new_pass2:
                        st.error("Passwords do not match.")
                    else:
                        result = client.create_user(
                            username=new_user,
                            password=new_pass,
                            display_name=new_display or new_user,
                        )
                        if result["ok"]:
                            st.success("Account created! You can now log in.")
                        else:
                            st.error(result["error"])

        # ── Connection status footer ──
        st.markdown("---")
        if client.connected:
            st.caption("✅ Neo4j connected")
        else:
            st.caption("❌ Neo4j offline — login requires a database connection")
            if client.error:
                st.caption(client.error)
