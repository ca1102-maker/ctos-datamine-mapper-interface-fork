# pages/training_mode.py
import streamlit as st
from datetime import datetime

# --- MODIFIED: Changed imports to use the correct absolute paths from the 'kg_toolkit' package root ---
from kg_toolkit.utils.llm_agent_4o import map_raw_data_isolated
from kg_toolkit.utils.data_manager import save_training_data
from kg_toolkit.utils.feedback_collector import collect_feedback_data

def show_training_mode():
    """Training mode page content"""
    st.title("🎯 Training Mode")
    st.markdown("Provide feedback on search results to improve the system")
    
    # Initialize session state for training data if it doesn't exist
    if 'training_data' not in st.session_state:
        st.session_state.training_data = []

    if 'agent_executor' not in st.session_state or not st.session_state.agent_executor:
        st.warning("⚠️ Agent has not been initialized. This can be done on the main app page.")
        return
    
    query = st.text_input(
        "Enter medical term for training:",
        value=st.session_state.get('current_query', ''),
        placeholder="e.g., patient age, chemotherapy regimen"
    )
    
    if st.button("🔍 Search for Training") or 'search_results' in st.session_state:
        if query:
            # Run a new search if the query is new or no results are stored
            if query != st.session_state.get('current_query') or 'search_results' not in st.session_state:
                with st.spinner("Getting results for training session..."):
                    try:
                        result = map_raw_data_isolated(
                            st.session_state.agent_executor,
                            st.session_state.system_prompt,
                            query
                        )
                        
                        st.session_state.current_query = query
                        st.session_state.search_results = {
                            'agent_response': result,
                            'query': query,
                            'timestamp': datetime.now()
                        }
                    except Exception as e:
                        st.error(f"Search failed: {str(e)}")
                        return
            
            # Display the training interface with the latest results
            show_training_interface()

def show_training_interface():
    """Display the training interface with feedback collection"""
    if 'search_results' not in st.session_state:
        return
    
    result = st.session_state.search_results['agent_response']
    query = st.session_state.search_results['query']
    
    st.markdown(f"### Training Session for: **{query}**")
    
    # This function currently uses mock data and needs to be implemented
    parsed_results = parse_agent_results(result, query)
    
    st.markdown("**Select the most relevant results:**")
    
    # This function is responsible for rendering checkboxes and collecting feedback
    feedback_data = collect_feedback_data(parsed_results)
    
    st.markdown("---")
    st.markdown("#### Additional Feedback")
    
    col1, col2 = st.columns(2)
    with col1:
        overall_quality = st.selectbox("Overall result quality:", 
                                     ["Excellent", "Good", "Fair", "Poor"])
    with col2:
        confidence_in_feedback = st.selectbox("Your confidence in this feedback:",
                                            ["Very Confident", "Confident", "Somewhat Confident", "Not Confident"])
    
    if st.button("💾 Save Training Data", type="primary"):
        training_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,

            'feedback': {
                'overall_quality': overall_quality,
                'confidence': confidence_in_feedback,
                **feedback_data
            },
            'agent_response': result
        }
        
        # Save the collected data using the data manager utility
        save_training_data(training_entry)
        st.session_state.training_data.append(training_entry)
        
        st.success("✅ Training data saved! Thank you for your feedback.")
        
        with st.expander("📊 Training Session Summary"):
            st.json(training_entry['feedback'])

def parse_agent_results(agent_response, query):
    """
    (Placeholder) Parses the raw agent response to extract individual tool results.
    This needs to be implemented to replace the mock data.
    """
    # TODO: Implement actual parsing of your agent's response string.
    # Look for tool execution patterns and observations in agent_response.
    
    mock_results = [
        {
            'id': f'result_1_{query}',
            'tool': 'exact_match',
            'content': f"Mock exact match analysis for: {query}",
            'score': 0.95,
            'source': 'agent_response'
        },
        {
            'id': f'result_2_{query}',
            'tool': 'semantic_search',
            'content': f"Mock semantic analysis for: {query}",
            'score': 0.82,
            'source': 'agent_response'
        }
    ]
    
    st.info("Note: Result parsing is currently using placeholder data.")
    return mock_results