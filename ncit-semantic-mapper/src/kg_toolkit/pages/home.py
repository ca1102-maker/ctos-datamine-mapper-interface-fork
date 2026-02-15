import streamlit as st
from datetime import datetime

from kg_toolkit.utils.llm_agent_4o import map_raw_data_isolated

def show_home_page():
    """Home page content for the Streamlit application."""
    st.markdown('<h1 class="main-header">SI-Tamer Home</h1>', unsafe_allow_html=True)

    # Quick search section
    st.markdown("### Quick Search")
    query = st.text_input("Enter medical term:", placeholder="e.g., lung cancer, hypertension")
    
    if st.button("Search") and query:
        # Check if the agent has been initialized in the main app and stored in session state
        if 'agent_executor' not in st.session_state or not st.session_state.agent_executor:
            st.error("Agent has not been initialized. Please ensure the main application has loaded the agent correctly.")
        else:
            with st.spinner(f"Searching for '{query}'..."):
                try:
                    # Call the agent function with the executor and prompt from the session state
                    result = map_raw_data_isolated(
                        st.session_state.agent_executor,
                        st.session_state.system_prompt,
                        query
                    )
                    
                    # Store the latest results in the session state
                    st.session_state.current_query = query
                    st.session_state.search_results = {
                        'agent_response': result,
                        'query': query,
                        'timestamp': datetime.now()
                    }
                    
                    st.markdown("### Quick Result")
                    
                    # If your agent returns JSON, this will need to be updated.
                    if "Final Answer:" in result:
                        final_section = result.split("Final Answer:")[-1].strip()
                        st.success("✅ Mapping found!")
                        with st.expander("View Result Details"):
                            st.text(final_section)
                            st.caption("For detailed results, switch to Training or Live Mode from the sidebar.")
                    else:
                        st.info("Search completed. View full results in Training or Live Mode.")
                        st.text(result) # Show the raw result if it's not in the expected format
                            
                except Exception as e:
                    st.error(f"An error occurred during the search: {str(e)}")