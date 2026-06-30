# streamlit_multipage_app.py
import streamlit as st
import os
from dotenv import load_dotenv

# Import the agent creation function from the 'utils' directory
from kg_toolkit.utils.llm_agent_4o import create_fresh_agent
# Import the page functions from the 'pages' directory
from kg_toolkit.pages.home import show_home_page
from kg_toolkit.pages.live_mode import show_live_mode
from kg_toolkit.pages.training_mode import show_training_mode

# Load environment variables from the .env file in the project root
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="SI-Tamer: Multi-Mode Medical Search",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization ---
def initialize_session_state():
    """Initializes all required session state variables."""
    # Using a loop to make it cleaner
    defaults = {
        'search_results': None,
        'current_query': "",
        'agent_executor': None,
        'system_prompt': None,
        'training_data': [],
        'mode_selection': "🏠 Home" # Default page
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# --- Main Application Logic ---
def main():
    """Main function to run the Streamlit app."""
    initialize_session_state()
    
    # --- Sidebar for Navigation and Agent Control ---
    with st.sidebar:
        st.title("🔬 SI-Tamer")
        st.markdown("---")
        
        st.markdown("**Backend Status**")
        neo4j_status = "✅ Connected" if os.getenv("NEO4J_URI") else "❌ Not Configured"
        openai_status = "✅ Connected" if os.getenv("OPENAI_API_KEY") else "❌ Not Configured"
        
        st.write(f"Neo4j: {neo4j_status}")
        st.write(f"OpenAI: {openai_status}")
        
        # Agent initialization button
        if st.button("🚀 Initialize Agent"):
            # Only Neo4j check is needed now
            if os.getenv("NEO4J_URI"):
                with st.spinner("Initializing agent..."):
                    try:
                        # This function now comes from llm_agent_4o.py
                        agent_executor, system_prompt = create_fresh_agent()
                        st.session_state.agent_executor = agent_executor
                        st.session_state.system_prompt = system_prompt
                        st.success("Agent is ready!")
                    except Exception as e:
                        st.error(f"Agent failed to initialize: {str(e)}")
            else:
                st.error("Missing Neo4j environment variables in .env file.")
        
        agent_ready = "🟢 Ready" if st.session_state.agent_executor else "🔴 Not Initialized"
        st.write(f"Agent Status: **{agent_ready}**")
        
        st.markdown("---")
        
        # Mode selection radio buttons
        mode = st.radio(
            "**Select Mode:**",
            ["🏠 Home", "🎯 Training Mode", "🚀 Live Mode"],
            key="mode_selection"
        )
    
    # --- Page Routing ---
    # Call the appropriate function based on the selected mode.
    # These functions are now imported from the 'pages' directory.
    if mode == "🏠 Home":
        show_home_page()
    elif mode == "🎯 Training Mode":
        show_training_mode()
    elif mode == "🚀 Live Mode":
        show_live_mode()

if __name__ == "__main__":
    main()