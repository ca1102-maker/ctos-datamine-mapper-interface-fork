"""
Frederick Platform — Streamlit entrypoint.

Run with:  streamlit run app/main.py
"""

import streamlit as st

st.set_page_config(
    page_title="Frederick Platform",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.styles import GLOBAL_CSS
from app.services.neo4j_client import get_client
from app.components.sidebar import render_sidebar
from app.views.home import page_home
from app.views.map_and_grade import page_map_and_grade
from app.views.graph_explore import page_graph_explore
from app.views.dashboard import page_dashboard
from app.views.ingest import page_ingest
from app.views.settings import page_settings
from app.views.benchmark import page_benchmark

# ── Global CSS ──
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── Session state defaults ──
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = []
if "settings" not in st.session_state:
    st.session_state.settings = {
        "dark_mode": False,
        "notifications": True,
        "api_endpoint": "https://api.frederick.ai",
    }
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = (
        "You are an expert medical data mapper specializing in NCIT terminology.\n"
        "Your job is to help map raw medical data values to standardized NCIT terms and codes.\n"
        "Be thorough but concise in your analysis. Always provide the recommended NCIT code and term if found."
    )
if "graph_query_history" not in st.session_state:
    st.session_state.graph_query_history = []

# ── Backend client (cached singleton) ──
@st.cache_resource
def _init_client():
    return get_client()

client = _init_client()

# ── Sidebar ──
render_sidebar(client)

# ── Router ──
page = st.session_state.page

if page == "Home":
    page_home(client)
elif page == "Map & Grade":
    page_map_and_grade(client)
elif page == "Explore Graph":
    page_graph_explore(client)
elif page == "Dashboard":
    page_dashboard(client)
elif page == "Ingest Data":
    page_ingest(client)
elif page == "Settings":
    page_settings(client)
elif page == "Benchmark":
    page_benchmark(client)
else:
    st.error(f"Unknown page: {page}")
    st.session_state.page = "Home"
    st.rerun()

# ── Footer ──
st.markdown("---")
st.caption("Frederick Platform v2.0.0 | Powered by Neo4j & LangChain | © 2025 Frederick AI")