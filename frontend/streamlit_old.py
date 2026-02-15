import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import math
import json
import io
import base64

# Page configuration
st.set_page_config(
    page_title="Frederick Semantic Mapping Platform",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme interface
st.markdown("""
    <style>
    /* Main app background */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1e 100%);
    }

    /* Override Streamlit's default backgrounds */
    .main {
        background-color: transparent;
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #16213e 0%, #0f1929 100%);
    }

    /* Headers */
    .main-header {
        font-size: 2rem;
        font-weight: 600;
        color: #4fc3f7;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #4fc3f7;
    }

    /* Cards and containers */
    .result-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        margin-bottom: 1rem;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #4fc3f7, #2196f3);
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.3s;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(79, 195, 247, 0.4);
    }

    /* Feedback boxes */
    .feedback-box {
        background: rgba(40, 167, 69, 0.1);
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 4px;
    }

    /* Links */
    .annotation-link {
        color: #4fc3f7;
        text-decoration: none;
        font-weight: 500;
    }

    .annotation-link:hover {
        text-decoration: underline;
        color: #29b6f6;
    }

    /* Metric boxes */
    .metric-box {
        background: rgba(255, 255, 255, 0.05);
        padding: 1.2rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Metrics text */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 600;
        color: #ffffff;
    }

    div[data-testid="stMetricDelta"] {
        color: #4fc3f7;
    }

    /* Score indicators */
    .mapping-score-high { color: #4caf50; font-weight: 600; }
    .mapping-score-medium { color: #ffc107; font-weight: 600; }
    .mapping-score-low { color: #f44336; font-weight: 600; }

    /* Input fields */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.05);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .stTextArea > div > div > textarea {
        background-color: rgba(255, 255, 255, 0.05);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .stSelectbox > div > div > div {
        background-color: rgba(255, 255, 255, 0.05);
        color: white;
    }

    /* Tables */
    .dataframe {
        background-color: rgba(255, 255, 255, 0.05);
        color: white;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        color: white;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(255, 255, 255, 0.05);
    }

    .stTabs [data-baseweb="tab"] {
        color: rgba(255, 255, 255, 0.7);
        background-color: transparent;
    }

    .stTabs [aria-selected="true"] {
        color: #4fc3f7;
        background-color: rgba(79, 195, 247, 0.1);
    }

    /* Chat messages */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #4fc3f7;
    }

    /* File uploader */
    .uploadedFile {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Make all text white by default */
    .markdown-text-container {
        color: white;
    }

    h1, h2, h3, h4, h5, h6, p, span, div {
        color: white;
    }

    /* Footer styling */
    .footer-box {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'mapping_results' not in st.session_state:
    st.session_state.mapping_results = None
if 'neo4j_data' not in st.session_state:
    st.session_state.neo4j_data = None
if 'feedback_history' not in st.session_state:
    st.session_state.feedback_history = []
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'current_query' not in st.session_state:
    st.session_state.current_query = ""


# Helper Functions
def export_data(data, format_type, filename_prefix):
    """Export data in various formats"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format_type == "CSV":
        csv = data.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename_prefix}_{timestamp}.csv">📥 Download CSV</a>'
        return href

    elif format_type == "TSV":
        tsv = data.to_csv(sep='\t', index=False)
        b64 = base64.b64encode(tsv.encode()).decode()
        href = f'<a href="data:file/tsv;base64,{b64}" download="{filename_prefix}_{timestamp}.tsv">📥 Download TSV</a>'
        return href

    elif format_type == "JSON":
        json_str = data.to_json(orient='records', indent=2)
        b64 = base64.b64encode(json_str.encode()).decode()
        href = f'<a href="data:file/json;base64,{b64}" download="{filename_prefix}_{timestamp}.json">📥 Download JSON</a>'
        return href


def generate_mock_neo4j_data(query, num_results=10):
    """Simulate Neo4j data retrieval"""
    concepts = [
        "Hypertension", "Diabetes Mellitus Type 2", "Chronic Kidney Disease",
        "Atrial Fibrillation", "Heart Failure", "COPD", "Asthma",
        "Migraine", "Depression", "Anxiety Disorder", "Pneumonia",
        "COVID-19", "Influenza", "Osteoarthritis", "Rheumatoid Arthritis"
    ]

    match_types = ["Exact", "Synonym", "Broader", "Narrower", "Related"]
    sources = ["SNOMED CT", "ICD-10", "LOINC", "RxNorm", "MedDRA"]

    data = []
    for i in range(num_results):
        score = random.uniform(0.65, 1.0)
        data.append({
            'Source Term': query,
            'Mapped Term': random.choice(concepts),
            'Match Type': random.choice(match_types),
            'Similarity Score': round(score, 3),
            'Confidence': 'High' if score > 0.9 else 'Medium' if score > 0.75 else 'Low',
            'Source': random.choice(sources),
            'Concept ID': f"{random.choice(['C', 'D', 'S'])}{random.randint(100000, 999999)}",
            'Semantic Type': random.choice(['Disease/Syndrome', 'Pharmacologic Substance',
                                            'Laboratory Procedure', 'Clinical Attribute']),
            'External Links': 'View in NCI | View in caDSR'
        })

    return pd.DataFrame(data)


def create_neo4j_visualization(data):
    """Create Neo4j-style graph visualization"""
    nodes = []
    edges = []

    # Central node (query term)
    central_term = data['Source Term'].iloc[0] if not data.empty else "Query"
    nodes.append({'id': 0, 'label': central_term, 'type': 'query', 'x': 0, 'y': 0})

    # Add mapped terms as nodes
    num_nodes = min(len(data), 15)
    for i in range(num_nodes):
        angle = 2 * math.pi * i / num_nodes
        radius = 2
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)

        nodes.append({
            'id': i + 1,
            'label': data.iloc[i]['Mapped Term'],
            'type': data.iloc[i]['Match Type'].lower(),
            'score': data.iloc[i]['Similarity Score'],
            'x': x,
            'y': y
        })

        edges.append({'source': 0, 'target': i + 1,
                      'weight': data.iloc[i]['Similarity Score']})

    return nodes, edges


def get_external_resource_links(term, concept_id, source):
    """Generate links to external terminology resources"""
    links = {
        'NCI Thesaurus': f"https://ncithesaurus.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code={concept_id}",
        'caDSR': f"https://cadsr.cancer.gov/onedata/dmdirect/NIH/NCI/CO/CDEDD?filter=Conceptual%20Domain%20Public%20ID={concept_id}",
        'UMLS': f"https://uts.nlm.nih.gov/uts/umls/concept/{concept_id}",
        'BioPortal': f"https://bioportal.bioontology.org/search?q={term.replace(' ', '+')}",
        'SNOMED Browser': f"https://browser.ihtsdotools.org/?perspective=full&conceptId1={concept_id}"
    }
    return links


# Sidebar Configuration
with st.sidebar:
    st.markdown("## 🔬 Semantic Mapping Platform")
    st.markdown("---")

    # Navigation
    page = st.selectbox(
        "Navigation",
        ["🎯 Semantic Mapping", "📊 Results Analysis", "🤖 AI Assistant",
         "🔗 Graph Visualization", "💬 Feedback Portal", "📈 Analytics Dashboard"]
    )

    st.markdown("---")

    # Configuration Settings
    with st.expander("⚙️ Mapping Configuration"):
        threshold = st.slider("Similarity Threshold", 0.0, 1.0, 0.75, 0.05,
                              help="Minimum similarity score for matches")
        max_results = st.number_input("Max Results", 5, 100, 20)
        terminology_source = st.multiselect(
            "Terminology Sources",
            ["SNOMED CT", "ICD-10", "LOINC", "RxNorm", "MedDRA", "NCI Thesaurus"],
            default=["SNOMED CT", "ICD-10"]
        )
        enable_fuzzy = st.checkbox("Enable Fuzzy Matching", value=True)
        include_synonyms = st.checkbox("Include Synonyms", value=True)

    st.markdown("---")

    # Quick Stats
    st.markdown("### 📊 Quick Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Mappings Today", "1,247", "↑ 12%")
    with col2:
        st.metric("Accuracy", "94.3%", "↑ 2.1%")

    st.markdown("---")

    # Export Section
    st.markdown("### 💾 Export Options")
    export_format = st.selectbox("Format", ["CSV", "TSV", "JSON"])

    if st.button("📥 Export Current Results"):
        if st.session_state.mapping_results is not None:
            download_link = export_data(
                st.session_state.mapping_results,
                export_format,
                "semantic_mapping"
            )
            st.markdown(download_link, unsafe_allow_html=True)
            st.success(f"✅ Export ready in {export_format} format")
        else:
            st.warning("No results to export")

# Main Content Area
if page == "🎯 Semantic Mapping":
    st.markdown('<h1 class="main-header">🎯 Semantic Term Mapping</h1>', unsafe_allow_html=True)

    # Input Section
    col1, col2 = st.columns([3, 1])
    with col1:
        query_input = st.text_area(
            "Enter terms to map (one per line):",
            placeholder="Enter medical terms, diagnoses, procedures, or medications...\nExample:\nHypertension\nType 2 Diabetes\nAspirin",
            height=120,
            value=st.session_state.current_query
        )

    with col2:
        st.markdown("### Mapping Options")
        map_direction = st.radio("Direction", ["Source → Target", "Bidirectional"])
        batch_mode = st.checkbox("Batch Processing", value=False)

    # Action Buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔍 Start Mapping", type="primary", use_container_width=True):
            if query_input:
                with st.spinner("Mapping terms..."):
                    import time

                    time.sleep(1.5)

                    # Generate mock results
                    terms = query_input.strip().split('\n')
                    all_results = []

                    for term in terms:
                        if term.strip():
                            results = generate_mock_neo4j_data(term.strip(), max_results)
                            all_results.append(results)

                    if all_results:
                        st.session_state.mapping_results = pd.concat(all_results, ignore_index=True)
                        st.session_state.current_query = query_input
                        st.success(f"✅ Mapped {len(terms)} term(s) successfully!")

    with col2:
        if st.button("🔄 Clear", use_container_width=True):
            st.session_state.mapping_results = None
            st.session_state.current_query = ""
            st.rerun()

    with col3:
        if st.button("📋 Load Example", use_container_width=True):
            st.session_state.current_query = "Hypertension\nDiabetes Mellitus\nCOVID-19"
            st.rerun()

    with col4:
        if st.button("⚡ Quick Map", use_container_width=True):
            st.info("Quick mapping uses cached results for faster processing")

    # Results Section
    if st.session_state.mapping_results is not None:
        st.markdown("---")
        st.markdown("### 📋 Mapping Results")

        # Sorting Options
        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            sort_by = st.selectbox("Sort by",
                                   ["Similarity Score", "Match Type", "Mapped Term", "Source"])
        with col2:
            sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)
        with col3:
            filter_confidence = st.multiselect("Filter by Confidence",
                                               ["High", "Medium", "Low"], default=["High", "Medium", "Low"])

        # Apply sorting and filtering
        df = st.session_state.mapping_results.copy()

        if filter_confidence:
            df = df[df['Confidence'].isin(filter_confidence)]

        ascending = sort_order == "Ascending"
        if sort_by == "Similarity Score":
            df = df.sort_values('Similarity Score', ascending=ascending)
        elif sort_by == "Match Type":
            df = df.sort_values('Match Type', ascending=ascending)
        elif sort_by == "Mapped Term":
            df = df.sort_values('Mapped Term', ascending=ascending)
        elif sort_by == "Source":
            df = df.sort_values('Source', ascending=ascending)

        # Display results with annotations
        st.markdown("#### Detailed Results Table")

        # Create annotated dataframe
        for idx, row in df.iterrows():
            with st.expander(f"🔗 {row['Source Term']} → {row['Mapped Term']} (Score: {row['Similarity Score']})"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**Match Type:** {row['Match Type']}")
                    st.markdown(f"**Source:** {row['Source']}")
                    st.markdown(f"**Concept ID:** {row['Concept ID']}")
                    st.markdown(f"**Semantic Type:** {row['Semantic Type']}")

                    # External links
                    links = get_external_resource_links(
                        row['Mapped Term'], row['Concept ID'], row['Source']
                    )
                    st.markdown("**External Resources:**")
                    link_cols = st.columns(5)
                    for i, (resource, url) in enumerate(links.items()):
                        with link_cols[i % 5]:
                            st.markdown(f"[{resource}]({url})")

                with col2:
                    # Confidence visualization
                    score = row['Similarity Score']
                    color = "#28a745" if score > 0.9 else "#ffc107" if score > 0.75 else "#dc3545"
                    st.markdown(f"### Confidence")
                    st.markdown(f"<h2 style='color: {color};'>{row['Confidence']}</h2>",
                                unsafe_allow_html=True)
                    st.progress(score)

        # Summary statistics
        st.markdown("---")
        st.markdown("#### Summary Statistics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Mappings", len(df))
        with col2:
            st.metric("Avg Score", f"{df['Similarity Score'].mean():.3f}")
        with col3:
            st.metric("High Confidence", f"{len(df[df['Confidence'] == 'High'])}")
        with col4:
            st.metric("Unique Sources", df['Source'].nunique())

        # Save results option
        st.markdown("---")
        if st.button("💾 Save Results to Database"):
            with st.spinner("Saving..."):
                import time

                time.sleep(1)
            st.success("✅ Results saved successfully!")

elif page == "📊 Results Analysis":
    st.markdown('<h1 class="main-header">📊 Results Analysis & Comparison</h1>', unsafe_allow_html=True)

    # Load or generate sample data for analysis
    if st.session_state.mapping_results is None:
        st.info("No current results. Loading sample data for demonstration...")
        st.session_state.mapping_results = generate_mock_neo4j_data("Sample Term", 50)

    df = st.session_state.mapping_results

    # Analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Distribution", "Comparison", "Trends", "Export"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Score Distribution")
            fig = go.Figure(data=[go.Histogram(
                x=df['Similarity Score'],
                nbinsx=20,
                marker_color='#3498db'
            )])
            fig.update_layout(
                xaxis_title="Similarity Score",
                yaxis_title="Frequency",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Match Type Distribution")
            match_counts = df['Match Type'].value_counts()
            fig = go.Figure(data=[go.Pie(
                labels=match_counts.index,
                values=match_counts.values,
                hole=0.4
            )])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Source Comparison")
        source_stats = df.groupby('Source').agg({
            'Similarity Score': ['mean', 'std', 'count']
        }).round(3)
        st.dataframe(source_stats, use_container_width=True)

    with tab3:
        st.subheader("Confidence Trends")
        confidence_data = df.groupby(['Confidence', 'Match Type']).size().reset_index(name='Count')
        fig = go.Figure()
        for conf in confidence_data['Confidence'].unique():
            data = confidence_data[confidence_data['Confidence'] == conf]
            fig.add_trace(go.Bar(name=conf, x=data['Match Type'], y=data['Count']))
        fig.update_layout(barmode='group', height=400)
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("Export Analysis Results")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📥 Export as CSV"):
                link = export_data(df, "CSV", "analysis_results")
                st.markdown(link, unsafe_allow_html=True)

        with col2:
            if st.button("📥 Export as TSV"):
                link = export_data(df, "TSV", "analysis_results")
                st.markdown(link, unsafe_allow_html=True)

        with col3:
            if st.button("📥 Export as JSON"):
                link = export_data(df, "JSON", "analysis_results")
                st.markdown(link, unsafe_allow_html=True)

elif page == "🤖 AI Assistant":
    st.markdown('<h1 class="main-header">🤖 Semantic Mapping AI Assistant</h1>', unsafe_allow_html=True)

    # AI Configuration
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        model = st.selectbox("Model", ["GPT-4 Medical", "Claude Medical", "BioGPT"])
    with col2:
        temperature = st.slider("Temperature", 0.0, 1.0, 0.3)
    with col3:
        context = st.text_input("Context", placeholder="e.g., oncology, cardiology, pediatrics...")

    # Chat interface
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "graph_data" in message:
                st.plotly_chart(message["graph_data"], use_container_width=True)

    # Chat input
    if prompt := st.chat_input("Ask about semantic mappings, terminology, or request Neo4j visualizations..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                import time

                time.sleep(1)

                # Check if user wants Neo4j data/visualization
                if any(keyword in prompt.lower() for keyword in ['neo4j', 'graph', 'visualize', 'show connections']):
                    st.markdown("I'll fetch that data from Neo4j for you...")

                    # Generate mock Neo4j data
                    neo4j_results = generate_mock_neo4j_data(prompt.split()[-1] if prompt.split() else "Term", 10)
                    nodes, edges = create_neo4j_visualization(neo4j_results)

                    # Create visualization
                    edge_x = []
                    edge_y = []
                    for edge in edges:
                        source = next(n for n in nodes if n['id'] == edge['source'])
                        target = next(n for n in nodes if n['id'] == edge['target'])
                        edge_x.extend([source['x'], target['x'], None])
                        edge_y.extend([source['y'], target['y'], None])

                    edge_trace = go.Scatter(
                        x=edge_x, y=edge_y,
                        line=dict(width=1, color='#888'),
                        hoverinfo='none',
                        mode='lines'
                    )

                    node_x = [n['x'] for n in nodes]
                    node_y = [n['y'] for n in nodes]
                    node_text = [n['label'] for n in nodes]
                    node_colors = ['#e74c3c' if n['type'] == 'query' else '#3498db' for n in nodes]

                    node_trace = go.Scatter(
                        x=node_x, y=node_y,
                        mode='markers+text',
                        text=node_text,
                        textposition="top center",
                        hoverinfo='text',
                        marker=dict(
                            color=node_colors,
                            size=20,
                            line_width=2
                        )
                    )

                    fig = go.Figure(data=[edge_trace, node_trace],
                                    layout=go.Layout(
                                        showlegend=False,
                                        hovermode='closest',
                                        margin=dict(b=0, l=0, r=0, t=0),
                                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                        height=400
                                    ))

                    st.plotly_chart(fig, use_container_width=True)

                    # Display tabular results
                    st.markdown("### Retrieved Neo4j Data:")
                    st.dataframe(neo4j_results, use_container_width=True)

                    response = f"I've retrieved and visualized the Neo4j data for your query. The graph shows {len(nodes) - 1} connected terms with their relationships and similarity scores."

                else:
                    response = f"""Based on your query about semantic mapping:

**Analysis:** I understand you're asking about "{prompt}". 

**Relevant Information:**
- Semantic mapping helps connect different terminology systems
- Common standards include SNOMED CT, ICD-10, and LOINC
- Similarity scores above 0.85 are generally considered strong matches

**Recommendations:**
1. Use fuzzy matching for slight variations
2. Consider context-specific mappings
3. Validate results with domain experts

Would you like me to fetch specific Neo4j data or create a visualization?"""

                st.markdown(response)
                st.session_state.chat_messages.append({"role": "assistant", "content": response})

elif page == "🔗 Graph Visualization":
    st.markdown('<h1 class="main-header">🔗 Neo4j Graph Visualization</h1>', unsafe_allow_html=True)

    # Graph controls
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        graph_type = st.selectbox("Graph Type", ["Terminology Network", "Concept Hierarchy", "Mapping Relations"])
    with col2:
        layout_type = st.selectbox("Layout", ["Force-Directed", "Hierarchical", "Circular"])
    with col3:
        depth = st.slider("Depth", 1, 5, 2)
    with col4:
        max_nodes_viz = st.number_input("Max Nodes", 10, 100, 30)

    # Query builder
    cypher_query = st.text_area(
        "Cypher Query:",
        value="MATCH (n:Term)-[r:MAPS_TO]->(m:Term) WHERE r.score > 0.75 RETURN n, r, m LIMIT 25",
        height=80
    )

    if st.button("🔍 Execute Query & Visualize"):
        with st.spinner("Fetching from Neo4j..."):
            import time

            time.sleep(1.5)

            st.success("✅ Query executed successfully")

            # Generate sample data for visualization
            sample_data = generate_mock_neo4j_data("Query Term", 15)
            nodes, edges = create_neo4j_visualization(sample_data)

            # Create visualization
            edge_x = []
            edge_y = []
            for edge in edges:
                source = next(n for n in nodes if n['id'] == edge['source'])
                target = next(n for n in nodes if n['id'] == edge['target'])
                edge_x.extend([source['x'], target['x'], None])
                edge_y.extend([source['y'], target['y'], None])

            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=1, color='#888'),
                hoverinfo='none',
                mode='lines'
            )

            node_x = [n['x'] for n in nodes]
            node_y = [n['y'] for n in nodes]
            node_text = [n['label'] for n in nodes]
            node_colors = ['#e74c3c' if n['type'] == 'query' else '#3498db' for n in nodes]

            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                text=node_text,
                textposition="top center",
                hoverinfo='text',
                marker=dict(
                    color=node_colors,
                    size=20,
                    line_width=2
                )
            )

            fig = go.Figure(data=[edge_trace, node_trace],
                            layout=go.Layout(
                                showlegend=False,
                                hovermode='closest',
                                margin=dict(b=0, l=0, r=0, t=0),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                height=500
                            ))

            st.plotly_chart(fig, use_container_width=True)

    # Graph statistics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Nodes", "2,847")
    with col2:
        st.metric("Relationships", "15,394")
    with col3:
        st.metric("Avg Degree", "5.4")
    with col4:
        st.metric("Clusters", "12")

elif page == "💬 Feedback Portal":
    st.markdown('<h1 class="main-header">💬 Expert Feedback Portal</h1>', unsafe_allow_html=True)

    st.markdown("""
    Your feedback helps us improve our semantic mapping accuracy and coverage. 
    Please share your expertise to enhance our system for all users.
    """)

    # Feedback form
    with st.form("feedback_form"):
        st.markdown("### Submit Feedback")

        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Name (Optional)", placeholder="Dr. Jane Smith")
            email = st.text_input("Email*", placeholder="doctor@hospital.org")
            organization = st.text_input("Organization", placeholder="Mayo Clinic")
            specialty = st.selectbox("Specialty",
                                     ["General Practice", "Cardiology", "Oncology", "Neurology",
                                      "Pediatrics", "Radiology", "Other"])

        with col2:
            feedback_type = st.selectbox("Feedback Type",
                                         ["Incorrect Mapping", "Missing Term", "Suggestion",
                                          "Bug Report", "Feature Request", "General Feedback"])
            priority = st.select_slider("Priority",
                                        ["Low", "Medium", "High", "Critical"])
            affected_terms = st.text_area("Affected Terms",
                                          placeholder="List the terms involved...")

        feedback_text = st.text_area("Detailed Feedback*",
                                     placeholder="Please describe the issue or suggestion in detail...",
                                     height=150)

        # Attachment option
        attachments = st.file_uploader("Attach Supporting Documents (Optional)",
                                       type=['pdf', 'docx', 'txt', 'csv'],
                                       accept_multiple_files=True)

        col1, col2 = st.columns([1, 3])
        with col1:
            submitted = st.form_submit_button("📤 Submit Feedback", type="primary")
        with col2:
            if submitted:
                if email and feedback_text:
                    # Store feedback
                    feedback_entry = {
                        'timestamp': datetime.now(),
                        'name': name or "Anonymous",
                        'email': email,
                        'organization': organization,
                        'specialty': specialty,
                        'type': feedback_type,
                        'priority': priority,
                        'feedback': feedback_text,
                        'attachments': len(attachments) if attachments else 0
                    }
                    st.session_state.feedback_history.append(feedback_entry)

                    st.success("✅ Thank you for your feedback! We'll review it within 24-48 hours.")
                    st.balloons()
                else:
                    st.error("Please fill in required fields (Email and Feedback)")

    # Previous feedback
    st.markdown("---")
    st.markdown("### Recent Feedback Submissions")

    if st.session_state.feedback_history:
        feedback_df = pd.DataFrame(st.session_state.feedback_history)

        # Display recent feedback
        for idx, feedback in enumerate(reversed(st.session_state.feedback_history[-5:])):
            with st.expander(
                    f"📝 {feedback['type']} - {feedback['timestamp'].strftime('%Y-%m-%d %H:%M')} - Priority: {feedback['priority']}"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**From:** {feedback['name']} ({feedback['organization']})")
                    st.markdown(f"**Specialty:** {feedback['specialty']}")
                    st.markdown(f"**Feedback:** {feedback['feedback']}")
                with col2:
                    st.markdown(f"**Status:** 🔄 Under Review")
                    if feedback['attachments'] > 0:
                        st.markdown(f"📎 {feedback['attachments']} attachment(s)")
    else:
        st.info("No feedback submissions yet")

    # Feedback statistics
    st.markdown("---")
    st.markdown("### Feedback Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Submissions", len(st.session_state.feedback_history))
    with col2:
        critical_count = sum(1 for f in st.session_state.feedback_history if f.get('priority') == 'Critical')
        st.metric("Critical Issues", critical_count)
    with col3:
        st.metric("Avg Response Time", "18 hours")
    with col4:
        st.metric("Resolution Rate", "92%")

elif page == "📈 Analytics Dashboard":
    st.markdown('<h1 class="main-header">📈 Analytics Dashboard</h1>', unsafe_allow_html=True)

    # Date range selector
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    # Key metrics
    st.markdown("### Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Total Mappings", "45,892", "↑ 15.3%",
                  help="Total semantic mappings performed")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Accuracy Rate", "94.3%", "↑ 2.1%",
                  help="Percentage of validated correct mappings")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Avg Response Time", "0.34s", "↓ 0.12s",
                  help="Average mapping query response time")
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Active Users", "287", "↑ 24",
                  help="Unique users in the last 24 hours")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Analytics tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Usage Trends", "Mapping Quality", "Term Coverage",
                                            "User Activity", "System Performance"])

    with tab1:
        st.subheader("Mapping Volume Over Time")

        # Generate time series data
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        volume_data = pd.DataFrame({
            'Date': dates,
            'Successful Mappings': np.random.randint(800, 1500, len(dates)) + np.arange(len(dates)) * 5,
            'Failed Mappings': np.random.randint(50, 150, len(dates)),
            'Partial Mappings': np.random.randint(100, 300, len(dates))
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=volume_data['Date'], y=volume_data['Successful Mappings'],
                                 mode='lines', name='Successful', line=dict(color='#28a745', width=3)))
        fig.add_trace(go.Scatter(x=volume_data['Date'], y=volume_data['Partial Mappings'],
                                 mode='lines', name='Partial', line=dict(color='#ffc107', width=2)))
        fig.add_trace(go.Scatter(x=volume_data['Date'], y=volume_data['Failed Mappings'],
                                 mode='lines', name='Failed', line=dict(color='#dc3545', width=2)))
        fig.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

        # Top mapped terms
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top Mapped Terms")
            top_terms = pd.DataFrame({
                'Term': ['Hypertension', 'Diabetes Type 2', 'COVID-19', 'Pneumonia', 'Asthma'],
                'Count': [2847, 2103, 1876, 1654, 1432]
            })
            st.dataframe(top_terms, use_container_width=True, hide_index=True)

        with col2:
            st.subheader("Mapping Sources Distribution")
            sources = pd.DataFrame({
                'Source': ['SNOMED CT', 'ICD-10', 'LOINC', 'RxNorm', 'MedDRA'],
                'Percentage': [35, 28, 20, 12, 5]
            })
            fig = go.Figure(data=[go.Pie(labels=sources['Source'], values=sources['Percentage'], hole=0.4)])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Mapping Quality Metrics")

        col1, col2 = st.columns(2)

        with col1:
            # Score distribution
            st.markdown("#### Similarity Score Distribution")
            scores = np.random.beta(8, 2, 1000)  # Skewed towards higher scores
            fig = go.Figure(data=[go.Histogram(x=scores, nbinsx=30, marker_color='#3498db')])
            fig.update_layout(
                xaxis_title="Similarity Score",
                yaxis_title="Frequency",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Confidence levels over time
            st.markdown("#### Confidence Levels Trend")
            dates_weekly = pd.date_range(start=start_date, end=end_date, freq='W')
            confidence_data = pd.DataFrame({
                'Date': dates_weekly,
                'High': np.random.randint(60, 70, len(dates_weekly)),
                'Medium': np.random.randint(20, 30, len(dates_weekly)),
                'Low': np.random.randint(5, 15, len(dates_weekly))
            })

            fig = go.Figure()
            fig.add_trace(go.Bar(x=confidence_data['Date'], y=confidence_data['High'],
                                 name='High', marker_color='#28a745'))
            fig.add_trace(go.Bar(x=confidence_data['Date'], y=confidence_data['Medium'],
                                 name='Medium', marker_color='#ffc107'))
            fig.add_trace(go.Bar(x=confidence_data['Date'], y=confidence_data['Low'],
                                 name='Low', marker_color='#dc3545'))
            fig.update_layout(barmode='stack', height=350)
            st.plotly_chart(fig, use_container_width=True)

        # Quality indicators
        st.markdown("#### Quality Indicators")
        quality_metrics = pd.DataFrame({
            'Metric': ['Precision', 'Recall', 'F1-Score', 'Coverage', 'Consistency'],
            'Value': [0.943, 0.912, 0.927, 0.856, 0.974],
            'Target': [0.95, 0.90, 0.92, 0.85, 0.97],
            'Status': ['🟡', '✅', '✅', '✅', '✅']
        })
        st.dataframe(quality_metrics, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Terminology Coverage Analysis")

        # Coverage by domain
        domains = ['Cardiology', 'Oncology', 'Neurology', 'Pediatrics', 'Radiology',
                   'Endocrinology', 'Infectious Disease', 'Psychiatry']
        coverage = [92, 88, 85, 90, 78, 83, 95, 72]

        fig = go.Figure(data=[go.Bar(
            x=coverage,
            y=domains,
            orientation='h',
            marker=dict(
                color=coverage,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Coverage %")
            )
        )])
        fig.update_layout(
            xaxis_title="Coverage Percentage",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Gap analysis
        st.markdown("#### Identified Gaps")
        gaps_data = pd.DataFrame({
            'Domain': ['Rare Diseases', 'Genomics', 'Traditional Medicine', 'Veterinary'],
            'Missing Terms': [342, 278, 456, 189],
            'Priority': ['High', 'Medium', 'Low', 'Low'],
            'Est. Completion': ['Q2 2025', 'Q3 2025', 'Q4 2025', 'Q1 2026']
        })
        st.dataframe(gaps_data, use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("User Activity Analysis")

        col1, col2 = st.columns(2)

        with col1:
            # User distribution by role
            st.markdown("#### Users by Role")
            roles = pd.DataFrame({
                'Role': ['Physicians', 'Researchers', 'Data Scientists', 'Administrators', 'Other'],
                'Count': [124, 89, 56, 12, 6]
            })
            fig = go.Figure(data=[go.Pie(labels=roles['Role'], values=roles['Count'])])
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Activity heatmap (simplified)
            st.markdown("#### Activity Heatmap")
            hours = list(range(24))
            activity = [random.randint(10, 100) for _ in hours]
            fig = go.Figure(data=[go.Bar(x=hours, y=activity, marker_color=activity,
                                         marker_colorscale='Reds')])
            fig.update_layout(
                xaxis_title="Hour of Day",
                yaxis_title="Activity Level",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

        # Top users
        st.markdown("#### Most Active Users")
        top_users = pd.DataFrame({
            'User': ['Dr. Smith', 'Dr. Johnson', 'Dr. Williams', 'Dr. Brown', 'Dr. Davis'],
            'Organization': ['Mayo Clinic', 'Johns Hopkins', 'Cleveland Clinic', 'UCSF', 'Mount Sinai'],
            'Mappings': [342, 298, 276, 245, 198],
            'Accuracy': ['96.2%', '94.8%', '97.1%', '93.5%', '95.9%']
        })
        st.dataframe(top_users, use_container_width=True, hide_index=True)

    with tab5:
        st.subheader("System Performance Metrics")

        col1, col2 = st.columns(2)

        with col1:
            # Response time
            st.markdown("#### Response Time (ms)")
            response_times = np.random.lognormal(5.5, 0.5, 100)
            fig = go.Figure(data=[go.Box(y=response_times, marker_color='#3498db')])
            fig.update_layout(yaxis_title="Response Time (ms)", height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # System load
            st.markdown("#### System Load")
            hours = list(range(24))
            cpu = [random.randint(30, 80) for _ in hours]
            memory = [random.randint(40, 70) for _ in hours]

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hours, y=cpu, mode='lines', name='CPU %',
                                     line=dict(color='#e74c3c', width=2)))
            fig.add_trace(go.Scatter(x=hours, y=memory, mode='lines', name='Memory %',
                                     line=dict(color='#3498db', width=2)))
            fig.update_layout(
                xaxis_title="Hour",
                yaxis_title="Usage %",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)

        # Error logs
        st.markdown("#### Recent System Events")
        events = pd.DataFrame({
            'Time': pd.date_range(end=datetime.now(), periods=5, freq='H'),
            'Event': ['Mapping service scaled up', 'Cache cleared', 'Database backup completed',
                      'API rate limit adjusted', 'Model updated to v2.3'],
            'Type': ['Info', 'Info', 'Success', 'Warning', 'Success'],
            'Impact': ['None', 'None', 'None', 'Minor', 'None']
        })
        st.dataframe(events, use_container_width=True, hide_index=True)

# Footer with export summary
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; padding: 2rem; background: rgba(255, 255, 255, 0.05); border-radius: 8px; margin-top: 2rem; border: 1px solid rgba(255, 255, 255, 0.1);'>
        <h4 style='color: #4fc3f7;'>Frederick Semantic Mapping Platform v2.0</h4>
        <p style='color: rgba(255, 255, 255, 0.8);'>Powered by Neo4j Graph Database | AI-Enhanced Terminology Mapping</p>
        <small style='color: rgba(255, 255, 255, 0.6);'>© 2025 Frederick Platform | Support: support@frederick.ai | Documentation: docs.frederick.ai</small>
    </div>
    """,
    unsafe_allow_html=True
)
